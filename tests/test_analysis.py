"""Validate real inputs and published results; no fabricated observations are exported."""
import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from analysis.core import ROOT, RAW, FACTOR, read_csv_auto, verify_2025, normalize, workbook_rows
from analysis.model import FEATURES, metrics
from analysis.core import FIELDS, TEXT, compact, numeric


def test_every_used_column_matches_official_workbook():
    csv, _ = read_csv_auto(RAW/'facilities_portal_download.csv')
    workbook = workbook_rows(2025)
    for key, (index, _, _) in FIELDS.items():
        workbook_index = index + 1 if index >= 37 else index
        a, b = csv.iloc[:, index], workbook.iloc[:, workbook_index]
        if key in TEXT:
            assert a.fillna('').map(compact).eq(b.fillna('').map(compact)).all(), key
        else:
            np.testing.assert_allclose(numeric(a), numeric(b), atol=.001, rtol=0, equal_nan=True, err_msg=key)


def test_original_source_hashes_have_not_changed():
    manifest = json.loads((ROOT/'data/processed/source_manifest.json').read_text(encoding='utf-8'))
    for item in manifest['files']:
        source = ROOT/item['path']
        assert source.stat().st_size == item['bytes']
        assert hashlib.sha256(source.read_bytes()).hexdigest() == item['sha256'], item['path']


@pytest.fixture(scope='module')
def result():
    return json.loads((ROOT/'public/data/analysis.json').read_text(encoding='utf-8'))


@pytest.fixture(scope='module')
def national():
    return pd.read_csv(ROOT/'data/processed/national_2025.csv')


def test_official_year_confirmed_by_full_census():
    raw, encoding = read_csv_auto(RAW/'facilities_portal_download.csv')
    verification=verify_2025(raw)
    assert encoding == 'utf-8-sig'
    assert verification['rows']==4556
    assert len(verification['columns'])==13
    assert all(v['matched']==4556 for v in verification['columns'].values())


def test_download_original_matches_provided_bytes():
    provided=next(p for p in RAW.glob('*.csv') if '공공하수처리시설' in p.name)
    assert hashlib.sha256(provided.read_bytes()).hexdigest()==hashlib.sha256((RAW/'facilities_portal_download.csv').read_bytes()).hexdigest()


def test_daily_flow_and_calendar_year_units(national):
    valid=national.inflow_m3_day.gt(0)
    np.testing.assert_allclose(national.loc[valid,'annual_inflow_m3'],national.loc[valid,'inflow_m3_day']*365)
    prev=pd.read_csv(ROOT/'data/processed/national_2024.csv')
    valid=prev.inflow_m3_day.gt(0)
    np.testing.assert_allclose(prev.loc[valid,'annual_inflow_m3'],prev.loc[valid,'inflow_m3_day']*366)


def test_intensity_and_bod_mass_balance(national):
    good=national.kwh_m3.notna()
    np.testing.assert_allclose(national.loc[good,'kwh_m3'],national.loc[good,'electricity_kwh']/national.loc[good,'annual_inflow_m3'])
    good=national.bod_removed_kg_est.notna()
    mass=(national.annual_inflow_m3*national.bod_in-national.annual_outflow_m3*national.bod_out)/1000
    np.testing.assert_allclose(national.loc[good,'bod_removed_kg_est'],mass[good])
    good=national.bod_removal_pct.notna()
    assert national.loc[good,'bod_removal_pct'].between(0,100).all()


def test_missing_energy_is_never_published_as_zero_intensity(national):
    missing=national.electricity_kwh.isna()|national.electricity_kwh.le(0)
    assert missing.any()
    assert national.loc[missing,'kwh_m3'].isna().all()
    assert not national.loc[missing,'benchmark_eligible'].any()


def test_composite_identity_and_region_counts(result,national):
    assert national.facility_id.is_unique
    assert len(national)==result['summary']['national']['n']
    assert len(result['facilities'])==39
    assert all(f['region']=='대구광역시' for f in result['facilities'])
    assert len(result['national'])==len(national)


def test_weighted_summary_uses_the_same_denominator_population(result,national):
    for label,frame in [('national',national),('daegu',national[national.is_daegu])]:
        x=frame.loc[frame.kwh_m3.notna()]
        assert result['summary'][label]['weighted_kwh_m3']==pytest.approx(x.electricity_kwh.sum()/x.annual_inflow_m3.sum())


def test_peers_are_independent_and_match_declared_conditions(result,national):
    byid=national.set_index('facility_id')
    for f in result['facilities']:
        peer=result['peers'][f['facility_id']]
        if not peer['available']:
            assert peer['reason'];continue
        assert 5<=peer['count']<=20
        rows=byid.loc[peer['peer_ids']]
        assert not rows.is_daegu.any()
        assert rows.benchmark_eligible.all()
        assert rows.process_key.eq(f['process_key']).all()
        for key in ['capacity_m3_day','inflow_m3_day','bod_load_kg_year']:
            assert (rows[key]/f[key]).between(.5,2).all()
        assert peer['median_kwh_m3']==pytest.approx(rows.kwh_m3.median())


def test_model_groups_and_daegu_holdout(result,national):
    folds=pd.read_csv(ROOT/'data/processed/model_fold_assignment.csv')
    assert set(folds.fold)==set(range(5))
    assert folds.facility_id.is_unique
    assert folds.groupby('group').fold.nunique().eq(1).all()
    daegu_ids=set(national.loc[national.is_daegu,'facility_id'])
    assert daegu_ids.isdisjoint(set(folds.facility_id))
    assert set(p['facility_id'] for p in result['model']['predictions'])<=daegu_ids
    assert set(FEATURES).isdisjoint({'electricity_kwh','indirect_tco2e_est','kwh_m3','kwh_kg_bod','self_sufficiency_pct'})
    assert len(folds)==result['model']['train_n']


def test_model_evaluation_recomputes_from_published_predictions(result):
    m=result['model'];p=m['predictions']
    for e in m['evaluations']:
        field={'Random Forest': 'rf_predicted', 'XGBoost': 'xgb_predicted'}.get(e['name'], 'baseline_predicted')
        score=metrics([x['actual'] for x in p],[x[field] for x in p])
        for key in ['mae','rmse','r2']:
            assert e['daegu'][key]==pytest.approx(score[key])
    assert m['selected']==min(m['evaluations'],key=lambda x:x['cv']['mae'])['name']


def test_all_oof_scores_reconstruct_with_identical_group_splits(result,national):
    m=result['model']
    oof=pd.read_csv(ROOT/'data/processed/model_oof_predictions.csv')
    eligible=national.loc[national.benchmark_eligible & ~national.is_daegu].set_index('facility_id')
    folds=pd.read_csv(ROOT/'data/processed/model_fold_assignment.csv').set_index('facility_id')
    assert set(oof.model)=={e['name'] for e in m['evaluations']}
    assert len(oof)==3*len(eligible)
    for e in m['evaluations']:
        rows=oof[oof.model.eq(e['name'])].set_index('facility_id')
        assert rows.index.is_unique
        assert set(rows.index)==set(eligible.index)
        assert rows.fold.eq(folds.loc[rows.index,'fold']).all()
        np.testing.assert_allclose(rows.actual,eligible.loc[rows.index,'kwh_m3'])
        for key,value in metrics(rows.actual,rows.predicted).items():
            assert e['cv'][key]==pytest.approx(value)
        for fold,score in enumerate(e['folds']):
            sample=rows[rows.fold.eq(fold)]
            for key,value in metrics(sample.actual,sample.predicted).items():
                assert score[key]==pytest.approx(value)


def test_preprocessing_medians_use_only_each_training_fold(result,national):
    train=national.loc[national.benchmark_eligible & ~national.is_daegu].copy().set_index('facility_id')
    train['log_capacity']=np.log1p(train.capacity_m3_day)
    train['log_inflow']=np.log1p(train.inflow_m3_day)
    folds=pd.read_csv(ROOT/'data/processed/model_fold_assignment.csv').set_index('facility_id')
    for audit in result['model']['preprocessing_audit']:
        training_ids=folds.index[folds.fold.ne(audit['fold'])]
        assert audit['train_n']==len(training_ids)
        expected=train.loc[training_ids,FEATURES[:-1]].median()
        for feature,value in audit['numeric_medians'].items():
            assert value==pytest.approx(expected[feature])


def test_xgboost_shap_scope_background_inputs_and_additivity(result,national):
    m=result['model']; s=m['shap']
    assert s['available'] and s['model']=='XGBoost'
    assert s['feature_perturbation']=='interventional'
    assert s['model_output']=='raw' and s['approximate'] is False
    assert s['scale']=='log(kWh/m³)'
    inputs=national.set_index('facility_id').copy()
    inputs['log_capacity']=np.log1p(inputs.capacity_m3_day)
    inputs['log_inflow']=np.log1p(inputs.inflow_m3_day)
    background=inputs.loc[s['background_facility_ids']]
    assert len(background)==s['background_n']==100
    assert background.index.is_unique and background.benchmark_eligible.all()
    assert not background.is_daegu.any()
    daegu=inputs.loc[inputs.is_daegu & inputs.benchmark_eligible]
    assert set(x['facility_id'] for x in s['predictions'])==set(daegu.index)
    assert s['n']==len(daegu)
    predictions={x['facility_id']:x for x in m['predictions']}
    values={key:[] for key in FEATURES}
    errors=[]
    for row in s['predictions']:
        assert row['base_value']==s['base_value']
        assert len(row['contributions'])==len(FEATURES)
        assert {x['key'] for x in row['contributions']}==set(FEATURES)
        reconstructed=row['base_value']+sum(x['shap_value'] for x in row['contributions'])
        error=abs(reconstructed-row['predicted_log']); errors.append(error)
        assert error==pytest.approx(row['additivity_error'],abs=1e-12)
        assert error<1e-5
        assert np.exp(reconstructed)==pytest.approx(row['reconstructed_predicted'])
        assert np.exp(reconstructed)==pytest.approx(row['predicted'],rel=2e-5)
        assert row['predicted']==pytest.approx(predictions[row['facility_id']]['xgb_predicted'])
        assert row['predicted_log']==pytest.approx(np.log(row['predicted']),abs=1e-6)
        magnitudes=[abs(x['shap_value']) for x in row['contributions']]
        assert magnitudes==sorted(magnitudes,reverse=True)
        assert [x['rank'] for x in row['contributions']]==list(range(1,8))
        for x in row['contributions']:
            original=inputs.loc[row['facility_id'],x['key']]
            if pd.isna(original): assert x['value'] is None
            elif isinstance(original,str): assert x['value']==original
            else: assert x['value']==pytest.approx(original)
            values[x['key']].append(x['shap_value'])
    assert s['max_additivity_error']==pytest.approx(max(errors),abs=1e-12)
    assert s['baseline_prediction']==pytest.approx(np.exp(s['base_value']))
    for rank,x in enumerate(s['importance'],1):
        assert x['rank']==rank
        assert x['mean_abs']==pytest.approx(np.abs(values[x['key']]).mean())
    assert [x['mean_abs'] for x in s['importance']]==sorted([x['mean_abs'] for x in s['importance']],reverse=True)
    saved=json.loads((ROOT/'data/processed/xgboost_shap.json').read_text(encoding='utf-8'))
    assert saved==s


def test_carbon_conversion_separate_from_reported_co2(result,national):
    positive=national.electricity_kwh.gt(0)
    np.testing.assert_allclose(national.loc[positive,'indirect_tco2e_est'],national.loc[positive,'electricity_kwh']/1000*FACTOR['value'])
    base=result['summary']['daegu']['electricity_kwh']
    scenarios=[base*rate/100/1000*FACTOR['value'] for rate in [0,10,30]]
    assert scenarios[0]==0
    assert scenarios[2]==pytest.approx(3*scenarios[1])
    assert scenarios[1]==pytest.approx(5919.600156)
    assert 'reported_co2_kg_m3' in national


def test_trends_only_verified_identical_facilities(result):
    previous=pd.read_csv(ROOT/'data/processed/national_2024.csv').set_index('match_key')
    for f in result['facilities']:
        trend=next(t for t in result['trends'] if t['facility_id']==f['facility_id'])
        r=previous.loc[f['match_key']]
        assert not isinstance(r,pd.DataFrame)
        assert ''.join(r.address.split())==''.join(f['address'].split())
        assert trend['electricity_previous']==pytest.approx(r.electricity_kwh)


def test_estimated_coordinates_are_labeled_and_traceable(result):
    verified=pd.read_csv(ROOT/'data/coordinates.csv')
    estimated=pd.read_csv(ROOT/'data/coordinates_estimated.csv')
    assert len(result['coordinates'])==len(verified)+len(estimated)
    assert result['quality']['coordinates_verified_n']==len(verified)
    assert result['quality']['coordinates_estimated_n']==len(estimated)
    by_id={row['facility_id']:row for row in result['coordinates']}
    for row in estimated.itertuples():
        displayed=by_id[row.facility_id]
        assert displayed['status']=='estimated'
        assert displayed['basis']==row.basis
        assert displayed['area_name']==row.area_name
        assert displayed['source_url']==row.source_url
        assert displayed['source_address']==row.source_address
        assert displayed['latitude']==pytest.approx(row.latitude)
        assert displayed['longitude']==pytest.approx(row.longitude)
        assert displayed['attribution']
    geo=json.loads((ROOT/'data/processed/facilities.geojson').read_text(encoding='utf-8'))
    assert len(geo['features'])==len(result['coordinates'])


def test_all_columns_and_report_downloads_are_auditable(result):
    assert len(result['quality']['columns'])==60
    for name in ['README.md','DATA_SOURCES.md','DATA_QUALITY_REPORT.md','ANALYSIS_REPORT.md','MODEL_EVALUATION.md','AI_PROMPT_LOG.md','PUBLIC_DATA_USAGE.md']:
        assert (ROOT/name).read_bytes()==(ROOT/'public/downloads'/name).read_bytes()
    for x in result['insights']:
        assert all(x.get(k) for k in ['value','comparison','policy','limitation','source','year'])


def test_no_nonstandard_nan_in_output():
    def reject(value): raise AssertionError(f'Invalid JSON number: {value}')
    json.loads((ROOT/'public/data/analysis.json').read_text(encoding='utf-8'),parse_constant=reject)
