"""Audit the newly collected API observations independently of the annual energy analysis."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from analysis.core import ROOT


@pytest.fixture(scope='module')
def api():
    data=json.loads((ROOT/'public/data/analysis.json').read_text(encoding='utf-8'))
    return data['operational_api']


@pytest.fixture(scope='module')
def daily():
    return pd.read_csv(ROOT/'data/processed/hasu_effluent_daily_2025.csv')


def test_full_year_and_actual_operation_date(api):
    meta=json.loads((ROOT/'data/raw/hasu_api/collection_2025.json').read_text(encoding='utf-8'))
    assert len(meta)==365 and all(x['complete'] for x in meta)
    assert api['request_days']==api['complete_request_days']==api['operation_days']==365
    assert api['start_date']=='2025-01-01' and api['end_date']=='2025-12-31'
    assert api['query_operation_day_offsets']=={'1':api['raw_records']}
    assert api['raw_records']==sum(x['collected_items_n'] for x in meta)


def test_selected_rows_are_unambiguous_effluent_mg_l(daily,api):
    assert daily.GDesc.eq('유입.방류수질').all()
    assert daily.SDesc.eq('방류수').all()
    assert set(daily.QDesc)=={'TOC(mg/L)','T-N(mg/L)','T-P(mg/L)','SS(mg/L)'}
    assert set(daily.unit)=={'mg/L'}
    assert pd.to_datetime(daily.opdate).dt.year.eq(2025).all()
    assert not daily.duplicated(['opdate','ouId','metric']).any()
    assert len(daily)==api['effluent_records']
    assert int(daily.value.notna().sum())==api['valid_effluent_records']


def test_monthly_means_counts_and_gaps_recompute(daily,api):
    for r in api['monthly']:
        x=daily.loc[daily.ouId.eq(r['site'])&daily.metric.eq(r['metric'])&daily.month.eq(r['month']),'value'].dropna()
        assert len(x)==r['valid_days']
        assert r['coverage_pct']==pytest.approx(100*len(x)/r['calendar_days'])
        if len(x):
            assert r['mean']==pytest.approx(x.mean())
            assert r['min']==pytest.approx(x.min())
            assert r['max']==pytest.approx(x.max())
        else:assert r['mean'] is None


def test_missing_meter_never_filled_from_bmeter(daily):
    # Missing observations in the real data are preserved even when BMeter supplies a different number.
    missing=pd.to_numeric(daily.meter.astype(str).str.replace(',','',regex=False),errors='coerce').isna()
    assert missing.any()
    assert daily.loc[missing,'value'].isna().all()
    assert daily.value.dropna().ge(0).all()


def test_annual_energy_boundary_unchanged_and_unknown_units_excluded(api):
    assert api['model_included'] is False
    assert api['energy_comparable'] is False
    assert api['coordinates_available'] is False
    assert api['electricity_labels']==[{'ouId':'북부사업소','GDesc':'전기사용','QDesc':'총인전력량(kw/일)'}]
    data=json.loads((ROOT/'public/data/analysis.json').read_text(encoding='utf-8'))
    assert data['summary']['daegu']['electricity_kwh']==pytest.approx(136711320)
    assert len(data['facilities'])==39


def test_secret_is_absent_from_sources_results_raw_and_bundle():
    env=ROOT/'.env.local'
    if not env.exists():pytest.skip('Local credential file intentionally not distributed')
    key=next((s.split('=',1)[1].strip() for s in env.read_text(encoding='utf-8').splitlines() if s.startswith('HASU_SERVICE_KEY=')),'')
    assert key
    allowed=[ROOT/'src',ROOT/'analysis',ROOT/'scripts',ROOT/'tests',ROOT/'data',ROOT/'public',ROOT/'dist']
    for folder in allowed:
        for path in folder.rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts:
                assert key.encode() not in path.read_bytes(),f'Credential leaked into {path.relative_to(ROOT)}'
    assert '.env*' in (ROOT/'.gitignore').read_text(encoding='utf-8')
    assert 'VITE_HASU' not in (ROOT/'.env.example').read_text(encoding='utf-8')


def test_failed_api_response_is_not_cached(tmp_path, monkeypatch):
    import scripts.hasu_api as client
    monkeypatch.setattr(client, 'RAW', tmp_path)
    monkeypatch.setattr(client, 'credential', lambda: 'test-only-placeholder')
    class Response:
        status_code=200
        content=b'<response><header><resultCode>99</resultCode></header><body/></response>'
    monkeypatch.setattr(client.requests, 'get', lambda *args, **kwargs: Response())
    record, items=client.request('2025-01-02')
    assert record['resultCode']=='99' and items==[]
    assert list(tmp_path.glob('*.xml'))==[]


def test_partial_api_collection_cannot_be_published(tmp_path, monkeypatch):
    import analysis.hasu as operational
    folder=tmp_path/'hasu_api';folder.mkdir()
    (folder/'collection_2025.json').write_text('[{"date":"2025-01-02","complete":false}]',encoding='utf-8')
    monkeypatch.setattr(operational,'RAW',tmp_path)
    with pytest.raises(RuntimeError,match='불완전'):
        operational.analyze_hasu()
