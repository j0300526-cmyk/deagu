"""Run with python -m analysis.pipeline. Network-free, deterministic analysis."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

import geopandas as gpd
import numpy as np
import pandas as pd

from .core import (ROOT, RAW, PROCESSED, PUBLIC, DAEGU, YEAR, FACTOR, FIELDS, TEXT,
                   read_csv_auto, numeric, compact, normalize, workbook_rows, verify_2025, peers_for)
from .model import run_model
from .hasu import analyze_hasu


def clean_json(value):
    if isinstance(value, dict): return {str(k): clean_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)): return [clean_json(v) for v in value]
    if isinstance(value, (np.integer,)): return int(value)
    if isinstance(value, (np.floating, float)): return float(value) if np.isfinite(value) else None
    if isinstance(value, (np.bool_,)): return bool(value)
    if value is pd.NA or value is pd.NaT: return None
    return value


def save_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(clean_json(obj), ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def summary(d):
    eligible = d.loc[d.kwh_m3.notna()]
    return {'n': len(d), 'energy_valid_n': int(d.electricity_kwh.gt(0).sum()),
            'intensity_valid_n': len(eligible), 'electricity_kwh': d.electricity_kwh.where(d.electricity_kwh.gt(0)).sum(),
            'annual_inflow_m3': eligible.annual_inflow_m3.sum(),
            'weighted_kwh_m3': eligible.electricity_kwh.sum() / eligible.annual_inflow_m3.sum(),
            'mean_kwh_m3': eligible.kwh_m3.mean(), 'median_kwh_m3': eligible.kwh_m3.median(),
            'median_bod_removal_pct': d.bod_removal_pct.median(),
            'indirect_tco2e_est': d.indirect_tco2e_est.sum(), 'benchmark_n': int(d.benchmark_eligible.sum())}


def supplementary(year):
    book = RAW / f'statistics_{year}_catalog.xlsx'
    result = {'year': year}
    for kind, sheet, fields in [
        ('sludge', '11-1. 하수찌꺼기 발생 및 처리 현황', {'generated_t_year': 4, 'self_generated_t_year': 5, 'treated_t_year': 10}),
        ('reuse', '10-1. 공공하수처리재이용', {'annual_treated_thousand_t': 6, 'reused_thousand_t_year': 15, 'reuse_pct': 33})]:
        d = pd.read_excel(book, sheet_name=sheet, header=None)
        # Prefer the official province total. Do not sum repeated printed subtotals.
        total = d.loc[d[0].eq(DAEGU) & d[2].eq('합계')].iloc[0]
        record = {k: pd.to_numeric(total[i], errors='coerce') for k, i in fields.items()}
        record['source_sheet'] = sheet
        record['unit_note'] = '原表: 톤/년·천톤/년. 시설 단위 모델에 지역 총량을 배분하지 않음.'
        if kind == 'reuse':
            record['reuse_pct'] = 100 * record['reused_thousand_t_year'] / record['annual_treated_thousand_t']
        result[kind] = record
    return result


def coordinates(d):
    verified = pd.read_csv(ROOT / 'data/coordinates.csv', dtype={'facility_id': str})
    estimated = pd.read_csv(ROOT / 'data/coordinates_estimated.csv', dtype={'facility_id': str})
    if verified.facility_id.duplicated().any() or estimated.facility_id.duplicated().any():
        raise ValueError('시설별 좌표 중복')
    verified = verified.loc[verified.verified.astype(str).str.lower().eq('true')].copy()
    verified['status'] = 'verified'
    verified['basis'] = '공식 시설 좌표'
    estimated = estimated.loc[estimated.status.eq('estimated')].copy()
    if len(estimated):
        actual = d.set_index('facility_id')
        if not estimated.facility_id.isin(actual.index).all():
            raise ValueError('추정 좌표에 알 수 없는 시설 ID가 있음')
        for row in estimated.itertuples():
            source = actual.loc[row.facility_id]
            if row.facility_name != source['name'] or row.source_address != source['address']:
                raise ValueError(f'추정 좌표의 시설명·주소가 분석 원본과 다름: {row.facility_id}')
    estimated = estimated.loc[~estimated.facility_id.isin(verified.facility_id)].copy()
    cols = ['facility_id', 'latitude', 'longitude', 'status', 'basis', 'area_name',
            'source_address', 'source_url', 'reference_year', 'attribution', 'note']
    parts = [frame.reindex(columns=cols) for frame in (verified, estimated) if len(frame)]
    coords = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=cols)
    if len(coords):
        coords.latitude = pd.to_numeric(coords.latitude, errors='coerce')
        coords.longitude = pd.to_numeric(coords.longitude, errors='coerce')
        if not (coords.latitude.between(35.5, 36.5) & coords.longitude.between(128.1, 128.9)
                & coords.source_url.fillna('').str.startswith('https://')
                & coords.facility_id.isin(d.facility_id)).all():
            raise ValueError('지도 좌표 범위·출처·시설 ID 검증 실패')
    if len(coords):
        g = gpd.GeoDataFrame(coords, geometry=gpd.points_from_xy(coords.longitude, coords.latitude), crs='EPSG:4326')
        geo = json.loads(g.to_json())
    else:
        g = gpd.GeoDataFrame({'facility_id': []}, geometry=[], crs='EPSG:4326')
        geo = json.loads(g.to_json())
    save_json(PROCESSED / 'facilities.geojson', geo)
    return coords.to_dict('records')


def run():
    PROCESSED.mkdir(parents=True, exist_ok=True); PUBLIC.mkdir(parents=True, exist_ok=True)
    raw, enc = read_csv_auto(RAW / 'facilities_portal_download.csv')
    verification = verify_2025(raw)
    save_json(PROCESSED / 'year_verification.json', verification)
    d = normalize(raw, YEAR)
    if d.facility_id.duplicated().any(): raise ValueError('시설 식별자 중복: 별도 정합성 검토 필요')
    prev = normalize(workbook_rows(2024), 2024, workbook=True)
    # 2024 carbon is not presented in a trend; use that year's approved reference factor in exported rows.
    prev['indirect_tco2e_est'] = prev.electricity_kwh.where(prev.electricity_kwh.gt(0)) * .4541 / 1000
    dg = d.loc[d.is_daegu].copy()
    national_summary, dg_summary = summary(d), summary(dg)
    national_screened = d.loc[d.benchmark_eligible]
    refs = {r.facility_id: peers_for(r, d) for _, r in dg.iterrows()}
    dg['rank_volume'] = dg.kwh_m3.rank(method='min')
    dg['rank_bod'] = dg.kwh_kg_bod.rank(method='min')
    dg['rank_change'] = dg.rank_volume - dg.rank_bod
    dg['national_percentile'] = dg.kwh_m3.map(lambda v: 100 * national_screened.kwh_m3.le(v).mean() if pd.notna(v) else np.nan)
    a = prev.loc[prev.is_daegu].copy()
    # Unambiguous names + district + unchanged normalized address; no fuzzy guesses.
    a = a.loc[~a.match_key.duplicated(keep=False)]
    b = dg.loc[~dg.match_key.duplicated(keep=False)]
    joined = b.merge(a, on='match_key', suffixes=('', '_previous'))
    joined = joined.loc[joined.address.map(compact).eq(joined.address_previous.map(compact))]
    trends = []
    for _, r in joined.iterrows():
        trends.append({'facility_id': r.facility_id, 'name': r['name'], 'previous_year': 2024, 'year': YEAR,
                       'electricity_previous': r.electricity_kwh_previous, 'electricity_current': r.electricity_kwh,
                       'intensity_previous': r.kwh_m3_previous, 'intensity_current': r.kwh_m3,
                       'energy_change_pct': (r.electricity_kwh / r.electricity_kwh_previous - 1) * 100 if r.electricity_kwh_previous > 0 else None})
    method_rows = []
    for method, group in national_screened.groupby('process_key'):
        if len(group) >= 5:
            method_rows.append({'method': method, 'n': len(group), 'median': group.kwh_m3.median(),
                                'q25': group.kwh_m3.quantile(.25), 'q75': group.kwh_m3.quantile(.75),
                                'median_bod_removal': group.bod_removal_pct.median()})
    scale_rows = []
    for scale in ['소규모 <500', '중소 500–1만', '중형 1만–10만', '대형 ≥10만']:
        x, y = national_screened.loc[national_screened.scale.eq(scale)], dg.loc[dg.scale.eq(scale) & dg.benchmark_eligible]
        scale_rows.append({'scale': scale, 'national_n': len(x), 'daegu_n': len(y),
                           'national_median': x.kwh_m3.median(), 'daegu_median': y.kwh_m3.median()})
    eligible_cor = national_screened[['capacity_m3_day', 'electricity_kwh', 'bod_removal_pct', 'kwh_m3', 'bod_in']]
    corr = eligible_cor.corr(method='spearman').to_dict()
    model = run_model(d)
    save_json(PROCESSED / 'model_results.json', model)
    if model.get('available'):
        pd.DataFrame(model['fold_assignment']).to_csv(PROCESSED / 'model_fold_assignment.csv', index=False, encoding='utf-8-sig')
        pd.DataFrame(model['predictions']).to_csv(PROCESSED / 'daegu_predictions.csv', index=False, encoding='utf-8-sig')
        pd.DataFrame(model['oof_predictions']).to_csv(PROCESSED / 'model_oof_predictions.csv', index=False, encoding='utf-8-sig')
        save_json(PROCESSED / 'xgboost_shap.json', model['shap'])
    # Every original column, including fields not used in analysis, is profiled.
    quality_columns = []
    index_fields = {v[0]: (k, v[2]) for k, v in FIELDS.items()}
    for i, col in enumerate(raw.columns):
        values = raw[col].astype(str).str.strip()
        missing = values.isin(['', '-', '미집계', 'N/A'])
        key, unit = index_fields.get(i, ('', '분석 미사용 / 단위 미확인'))
        invalid_numeric = int((~missing & numeric(values).isna()).sum()) if key and key not in TEXT else None
        quality_columns.append({'original': col, 'standard': key or None, 'unit': unit, 'missing_n': int(missing.sum()),
                                'missing_pct': 100 * missing.mean(), 'parse_failure_n': invalid_numeric})
    files = []
    for p in sorted(RAW.rglob('*.csv')):
        f, encoding = read_csv_auto(p)
        files.append({'file': str(p.relative_to(ROOT)).replace('\\', '/'), 'rows': len(f), 'columns': len(f.columns),
                      'encoding': encoding, 'year_min': pd.to_numeric(f.get('년도', pd.Series(dtype=float)), errors='coerce').min(),
                      'year_max': pd.to_numeric(f.get('년도', pd.Series(dtype=float)), errors='coerce').max(),
                      'missing': {c: {'n': int(f[c].str.strip().eq('').sum()), 'pct': 100*f[c].str.strip().eq('').mean()} for c in f.columns},
                      'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
    flags = d.explode('flags').dropna(subset=['flags']).groupby('flags').size().to_dict()
    quality = {'year': YEAR, 'encoding': enc, 'rows': len(d), 'daegu_rows': len(dg),
               'column_count': len(raw.columns), 'columns': quality_columns, 'files': files,
               'flags': flags, 'flagged_n': int(d['flags'].map(len).gt(0).sum()),
               'benchmark_n': len(national_screened), 'daegu_benchmark_n': int(dg.benchmark_eligible.sum()),
               'duplicates_composite': int(d.facility_id.duplicated().sum()),
               'duplicate_region_district_name': int(d.match_key.duplicated(keep=False).sum()),
               'coordinates_n': 0, 'year_verification': verification,
               'units_verified': True, 'previous_year_rows': len(prev),
               'previous_year_note': '2024 XLSX 개별행 중 소재지가 있는 4,468행. 공표 합계 4,469개소와 1개 차이가 있어 전국 증감률은 산출하지 않음.'}
    coords = coordinates(dg); quality['coordinates_n'] = len(coords)
    quality['coordinates_verified_n'] = sum(c['status'] == 'verified' for c in coords)
    quality['coordinates_estimated_n'] = sum(c['status'] == 'estimated' for c in coords)
    save_json(PROCESSED / 'data_quality.json', quality)
    for name, frame in [('national_2025', d), ('daegu_2025', dg), ('national_2024', prev)]:
        export = frame.copy(); export['flags'] = export['flags'].map(lambda x: '; '.join(x))
        export.to_csv(PROCESSED / f'{name}.csv', index=False, encoding='utf-8-sig')
    manifest = [{'path': str(p.relative_to(ROOT)).replace('\\', '/'), 'bytes': p.stat().st_size,
                 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(RAW.rglob('*')) if p.is_file()]
    save_json(PROCESSED / 'source_manifest.json', {'retrieved_on': '2026-11-13', 'files': manifest})
    supplement = supplementary(YEAR)
    operational_api = analyze_hasu()
    insights = make_insights(dg, dg_summary, national_summary, refs, scale_rows, trends)
    scatter_fields = ['facility_id','name','region','district','year','capacity_m3_day','inflow_m3_day','electricity_kwh',
                      'kwh_m3','kwh_kg_bod','bod_removal_pct','bod_in','tn_in','tp_in','method','process_key','scale','benchmark_eligible']
    data = {'meta': {'year': YEAR, 'previous_year': 2024, 'verified_on': '2026-11-13',
                     'source_ids': ['3073222', '15137402', '3045606'], 'factor': FACTOR,
                     'volume_definition': '일평균 유입하수량 × 해당 연도 일수. 실제 연간 계측 적산량과 구분한 유입량 기준 환산량.',
                     'mass_definition': '(연간 환산 유입량 × 유입 BOD − 연간 환산 방류량 × 방류 BOD) / 1,000. 연평균값 곱에 따른 근사량.',
                     'peer_definition': '동일 처리공법 조합, 용량·유입량·유입 BOD 부하 각각 0.5–2배인 타 지역 시설. 로그 거리로 가까운 최대 20개, 최소 5개.',
                     'source_url': 'https://www.data.go.kr/data/3073222/fileData.do',
                     'statistics_url': 'https://www.mcee.go.kr/home/web/public_info/read.do?publicInfoId=640&menuId=10123',
                     'limitations': ['단면 관측의 연관성으로 인과관계를 입증하지 않음.', '계통구매 전력과 자체발전 사용량이 구분되지 않아 간접배출은 표준화 추정량.',
                                     '공법명 일치가 동일 설계·방류기준·슬러지처리 범위를 보증하지 않음.', 'BOD 제거율만으로 법정 방류수 기준 충족을 판단하지 않음.']},
            'summary': {'daegu': dg_summary, 'national': national_summary},
            'facilities': dg.to_dict('records'), 'national': d[scatter_fields].to_dict('records'),
            'peers': refs, 'scale_comparison': scale_rows,
            'method_comparison': sorted(method_rows, key=lambda x: x['n'], reverse=True),
            'correlations': corr, 'trends': trends, 'model': {k:v for k,v in model.items() if k not in ['fold_assignment', 'oof_predictions']},
            'quality': quality, 'coordinates': coords, 'supplementary': supplement,
            'insights': insights, 'operational_api': operational_api}
    save_json(PUBLIC / 'analysis.json', data)
    from .reports import write_reports
    write_reports(clean_json(data), clean_json(manifest))
    print(json.dumps(clean_json({'year': YEAR, 'daegu': dg_summary, 'national': national_summary,
                                'peers_available': sum(v['available'] for v in refs.values()),
                                'model': model.get('evaluations'), 'insights': insights}), ensure_ascii=True, indent=2))


def make_insights(dg, ds, ns, peers, scales, trends):
    top = dg.nlargest(5, 'electricity_kwh')
    share = top.electricity_kwh.sum()/ds['electricity_kwh']*100
    valid_peers = [(r, peers[r.facility_id]) for _, r in dg.iterrows() if peers[r.facility_id]['available']]
    worst = max(valid_peers, key=lambda x:x[1]['ratio']) if valid_peers else None
    insights = [
        {'title': '시설 평균과 도시 전체 효율은 다른 질문이다',
         'value': f"{ds['weighted_kwh_m3']:.3f}", 'unit': 'kWh/m³ · 대구 가중 원단위',
         'finding': f"대구 {ds['intensity_valid_n']}개 시설의 단순 평균은 {ds['mean_kwh_m3']:.3f}, 유입량 가중 원단위는 {ds['weighted_kwh_m3']:.3f} kWh/m³이다. 전국 전체 가중 원단위는 {ns['weighted_kwh_m3']:.3f} kWh/m³이다.",
         'comparison': '2025년 전국·대구, 양의 유입량과 전력량이 모두 있는 시설. 가중 원단위 = 전력 합계 / 유입량 합계.',
         'policy': '도시 총량 관리는 유량 가중 지표로, 개별 시설 진단은 규모·공법·부하를 맞춰 평가한다.',
         'limitation': '대구와 전국의 시설 규모 구성이 다르므로 전체 평균 차이는 지역 운영성과의 인과적 차이가 아니다.'},
        {'title': '총량 정책은 전력 사용이 집중된 시설에서 시작한다', 'value': f'{share:.1f}%', 'unit': '상위 5개 시설 전력 비중',
         'finding': f"{', '.join(top['name'])} 등 상위 5개 시설이 대구 전력량의 {share:.1f}%를 사용한다. 합계 {top.electricity_kwh.sum()/1e6:.2f} GWh/년이다.",
         'comparison': '2025년 대구 전체 양의 연간 총전력사용량 대비 비중.',
         'policy': '총량 감축 검토는 대형 시설의 공정별 계측·송풍기 운전·슬러지 처리 에너지 경계 확인부터 시작한다.',
         'limitation': '전력 사용 총량이 크다는 사실은 비효율을 뜻하지 않는다. 처리량·고도처리 의무를 함께 고려해야 한다.'},
    ]
    if worst:
        r, p = worst
        insights.append({'title': '같은 공법과 유사 부하에서도 추가 진단 여지는 다르다',
                         'value': f"{p['ratio']:.2f}×", 'unit': f"{r['name']} / 비교집단 중앙값",
                         'finding': f"{r['name']}의 {r.kwh_m3:.3f} kWh/m³는 타 지역 유사 시설 {p['count']}개의 중앙값 {p['median_kwh_m3']:.3f} 대비 {p['ratio']:.2f}배다. BOD 농도 제거율은 {r.bod_removal_pct:.2f}%이다.",
                         'comparison': '동일 공법 조합, 용량·유입량·BOD 부하 각각 0.5–2배. 최소 5개, 최대 20개.',
                         'policy': '비효율 판정 대신 운영기관과 전력계측 범위, 추가 연계처리, 방류 T-N·T-P 조건을 확인하는 정밀진단 대상으로 검토한다.',
                         'limitation': '비교집단 중앙값은 해당 시설의 달성 가능한 목표가 아니며, 미관측 조건과 표본 선택의 영향을 받는다.'})
    ranked = dg.dropna(subset=['rank_volume','rank_bod']).copy()
    moved = ranked.loc[ranked.rank_change.abs().idxmax()]
    insights.append({'title': '물의 양을 볼 때와 제거한 오염을 볼 때 순위가 달라진다',
                     'value': f"{int(moved.rank_volume)} → {int(moved.rank_bod)}", 'unit': f"{moved['name']} · 대구 내 순위",
                     'finding': f"{moved['name']}은 유입량당 전력 기준 {int(moved.rank_volume)}위에서 BOD 제거 근사질량당 전력 기준 {int(moved.rank_bod)}위로 바뀐다. 두 지표는 각각 {moved.kwh_m3:.3f} kWh/m³, {moved.kwh_kg_bod:.2f} kWh/kg-BOD이다.",
                     'comparison': f"2025년 대구 중 두 지표 계산이 가능한 {len(ranked)}개 시설, 낮은 값이 1위. 동률은 공동 순위.",
                     'policy': '저농도 유입·불명수 영향을 점검하고 처리량 지표와 오염제거량 지표를 나란히 공개한다.',
                     'limitation': 'BOD 질량은 연평균 유량·농도의 곱으로 근사했다. 강우·시간별 변동과 질소·인 제거 에너지를 완전히 반영하지 않는다.'})
    potential = ds['electricity_kwh'] * .1 * FACTOR['value']/1000
    insights.append({'title': '10% 절감 가정은 실행계획을 검토하는 출발점이다',
                     'value': f'{potential:,.0f}', 'unit': 'tCO₂eq/년 · 가정 시나리오',
                     'finding': f"2025년 전력량에서 일률 10% 절감을 가정하면 {ds['electricity_kwh']*.1/1e6:.2f} GWh/년, 공식 계수 환산 {potential:,.1f} tCO₂eq/년이다.",
                     'comparison': '대구 총전력량(kWh/년) ÷ 1,000 × 10% × 0.4330 tCO₂eq/MWh (2025 승인, 2021–2023 평균, 소비단).',
                     'policy': '시설별 현장 진단과 수질 유지 검증 후 실현 가능한 절감률·투자비·계통전력 대체량을 별도로 산정한다.',
                     'limitation': '실증 감축·예측 성과가 아니다. 직접 CH₄·N₂O, 약품·슬러지·건설 배출은 포함하지 않는다.'})
    return [dict(x, year=YEAR, source='3073222 + 환경부 2025 하수도통계 전수 대조; 탄소: GIR 2025 승인 계수') for x in insights]


if __name__ == '__main__': run()
