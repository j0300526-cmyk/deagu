from __future__ import annotations

import calendar
import hashlib
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
PROCESSED = ROOT / 'data/processed'
PUBLIC = ROOT / 'public/data'
YEAR = 2025
DAEGU = '대구광역시'
SOURCE_URL = 'https://www.data.go.kr/data/3073222/fileData.do'
CATALOG_URL = 'https://www.mcee.go.kr/home/web/public_info/read.do?publicInfoId=640&menuId=10123'
GIR_URL = 'https://www.gir.go.kr/home/board/read.do?boardMasterId=2&boardId=86&menuId=36'
FACTOR = {'value': 0.4330, 'unit': 'tCO₂eq/MWh', 'approval_year': 2025,
          'statistics_period': '2021–2023년 평균', 'boundary': '소비단 / CO₂·CH₄·N₂O 합산',
          'source_url': GIR_URL,
          'note': '2025년 승인 공식 계수로 환산한 표준화 추정량. 2025년 실시간·연도별 전력믹스 계수가 아니며 법정 명세서 산정 적합성을 보증하지 않음. 총전력 중 계통구매량 구분 불가.'}

# CSV column indices are checked against the official workbook, never guessed by values.
FIELDS = {
    'region': (0, '시도', ''), 'district': (1, '구군', ''), 'name': (3, '시설명', ''),
    'address': (4, '소재지', ''), 'capacity_m3_day': (5, '시설용량', 'm³/일'),
    'inflow_m3_day': (9, '유입하수량', 'm³/일'), 'outflow_m3_day': (13, '방류량', 'm³/일'),
    'bod_in': (17, '유입 BOD', 'mg/L'), 'bod_out': (18, '방류 BOD', 'mg/L'),
    'toc_in': (19, '유입 TOC', 'mg/L'), 'toc_out': (20, '방류 TOC', 'mg/L'),
    'tn_in': (23, '유입 T-N', 'mg/L'), 'tn_out': (24, '방류 T-N', 'mg/L'),
    'tp_in': (25, '유입 T-P', 'mg/L'), 'tp_out': (26, '방류 T-P', 'mg/L'),
    'method': (31, '처리방법', ''), 'linked_feces': (33, '연계처리량 분뇨', 'm³/일'),
    'linked_livestock': (34, '연계처리량 축산', 'm³/일'),
    'linked_leachate': (35, '연계처리량 침출수', 'm³/일'),
    'linked_other': (36, '연계처리량 기타', 'm³/일'), 'started': (38, '가동개시일', '날짜'),
    'self_sufficiency_pct': (47, '에너지자립율', '%'),
    'energy_production_toe': (48, '에너지 자체생산량', 'TOE/년'),
    'electricity_kwh': (50, '연간 총전력사용량', 'kWh/년'),
    'reported_co2_kg_m3': (52, '원자료 하수처리량당 CO₂ 배출량', 'kgCO₂/m³'),
}
TEXT = {'region', 'district', 'name', 'address', 'method', 'started'}


def read_csv_auto(path: Path) -> tuple[pd.DataFrame, str]:
    for encoding in ['utf-8-sig', 'cp949', 'euc-kr']:
        try:
            frame = pd.read_csv(path, encoding=encoding, dtype=str, keep_default_na=False)
            frame.columns = [re.sub(r'\s+', ' ', str(c)).strip() for c in frame.columns]
            return frame, encoding
        except UnicodeError:
            continue
    raise ValueError(f'지원 인코딩으로 읽을 수 없음: {path}')


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.strip().str.replace(',', '', regex=False)
                         .replace({'-': '', '미집계': '', 'N/A': ''}), errors='coerce')


def compact(value: object) -> str:
    return re.sub(r'\s+', '', str(value)).strip()


def workbook_rows(year: int) -> pd.DataFrame:
    d = pd.read_excel(RAW / f'statistics_{year}_catalog.xlsx',
                      sheet_name='6. 공공하수처리시설(전체)', header=None)
    # No totals, year summary lines, or header lines. Missing-address rows are quarantined.
    mask = numeric(d[5]).gt(0) & d[4].notna() & d[3].notna() & d[2].ne('합계')
    return d.loc[mask].reset_index(drop=True)


def verify_2025(csv: pd.DataFrame) -> dict:
    x = workbook_rows(2025)
    if len(x) != len(csv): raise ValueError('CSV/XLSX 행 수 불일치: 분석연도 확정 불가')
    columns = {}
    for ci, xi in [(0, 0), (3, 3), (4, 4), (5, 5), (9, 9), (13, 13),
                   (17, 17), (18, 18), (19, 19), (23, 23), (25, 25), (31, 31), (50, 51)]:
        if ci in [0, 3, 4, 31]:
            equal = csv.iloc[:, ci].fillna('').map(compact).eq(x.iloc[:, xi].fillna('').map(compact))
        else:
            a, b = numeric(csv.iloc[:, ci]), numeric(x.iloc[:, xi])
            equal = (a - b).abs().lt(.001) | (a.isna() & b.isna())
        columns[csv.columns[ci]] = {'matched': int(equal.sum()), 'total': len(csv)}
        if not equal.all(): raise ValueError(f'2025 원본 대조 실패: {csv.columns[ci]}')
    return {'status': 'verified', 'year': 2025, 'rows': len(csv), 'columns': columns,
            'evidence': '공식 2025 XLSX의 개별 시설행과 13개 필드 전수 대조. 문자열 공백 정규화, 수치 허용오차 0.001.'}


def normalize(raw: pd.DataFrame, year: int, workbook: bool = False) -> pd.DataFrame:
    d = pd.DataFrame(index=raw.index)
    for key, (index, _, _) in FIELDS.items():
        xi = index + 1 if workbook and index >= 37 else index
        d[key] = raw.iloc[:, xi].astype('string').fillna('').astype(str).str.strip()
        if key not in TEXT: d[key] = numeric(d[key])
    for k in TEXT:
        d[k] = d[k].str.replace(r'\s+', ' ', regex=True)
    d['name_key'] = d['name'].map(compact)
    # Composite identity is conservative; names alone are not unique nationally.
    d['facility_id'] = d.apply(lambda r: hashlib.sha256('|'.join(compact(r[k]) for k in
                                  ['region', 'district', 'name', 'address']).encode()).hexdigest()[:14], axis=1)
    d['match_key'] = d.apply(lambda r: '|'.join(compact(r[k]) for k in ['region', 'district', 'name']), axis=1)
    d['year'] = year
    d['is_daegu'] = d.region.eq(DAEGU)
    d['process_key'] = d.method.map(lambda s: ','.join(sorted(set(
        t for t in re.split(r'[,/;+·]+', compact(s).upper().replace('A²O', 'A2O')) if t))))
    d['scale'] = pd.cut(d.capacity_m3_day, [0, 500, 10000, 100000, np.inf],
                        labels=['소규모 <500', '중소 500–1만', '중형 1만–10만', '대형 ≥10만'], right=False).astype(str)
    return derive(d)


def derive(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    days = 366 if calendar.isleap(int(d.year.iloc[0])) else 365
    positive_flow = d.inflow_m3_day.gt(0)
    positive_energy = d.electricity_kwh.gt(0)
    d['annual_inflow_m3'] = (d.inflow_m3_day * days).where(positive_flow)
    d['annual_outflow_m3'] = (d.outflow_m3_day * days).where(d.outflow_m3_day.ge(0))
    d['kwh_m3'] = (d.electricity_kwh / d.annual_inflow_m3).where(positive_energy & positive_flow)
    d['utilization_pct'] = (100 * d.inflow_m3_day / d.capacity_m3_day).where(d.capacity_m3_day.gt(0))
    for p in ['bod', 'toc', 'tn', 'tp']:
        valid = d[f'{p}_in'].gt(0) & d[f'{p}_out'].ge(0) & d[f'{p}_out'].le(d[f'{p}_in'])
        d[f'{p}_removal_pct'] = (100 * (1 - d[f'{p}_out'] / d[f'{p}_in'])).where(valid)
    d['bod_load_kg_year'] = (d.annual_inflow_m3 * d.bod_in / 1000).where(d.bod_in.gt(0))
    # Annual mean flow times annual mean concentration: approximate mass, not integrated measured mass.
    mass = (d.annual_inflow_m3 * d.bod_in - d.annual_outflow_m3 * d.bod_out) / 1000
    d['bod_removed_kg_est'] = mass.where(mass.gt(0) & d.bod_removal_pct.notna())
    d['kwh_kg_bod'] = (d.electricity_kwh / d.bod_removed_kg_est).where(positive_energy)
    d['indirect_tco2e_est'] = (d.electricity_kwh * FACTOR['value'] / 1000).where(positive_energy)
    started = pd.to_datetime(d.started, errors='coerce')
    d['age_years'] = ((pd.Timestamp(int(d.year.iloc[0]), 12, 31) - started).dt.days / 365.25)
    d.loc[d.age_years.lt(0), 'age_years'] = np.nan
    flags = []
    for _, r in d.iterrows():
        f = []
        if not (r.electricity_kwh > 0): f.append('전력 결측 또는 0 이하')
        if not (r.inflow_m3_day > 0): f.append('유입량 결측 또는 0 이하')
        if pd.notna(r.kwh_m3) and (r.kwh_m3 < .02 or r.kwh_m3 > 10): f.append('전력원단위 검토 범위 밖')
        if pd.notna(r.utilization_pct) and r.utilization_pct > 250: f.append('용량 대비 유입량 250% 초과')
        if pd.notna(r.utilization_pct) and r.utilization_pct < 5: f.append('용량 대비 유입량 5% 미만')
        if pd.isna(r.bod_removal_pct): f.append('BOD 제거율 계산 불가')
        if not r.process_key: f.append('처리공법 결측')
        flags.append(f)
    d['flags'] = flags
    d['benchmark_eligible'] = d.kwh_m3.notna() & d['flags'].map(len).eq(0) & d.bod_load_kg_year.gt(0)
    return d


def peers_for(row: pd.Series, pool: pd.DataFrame, min_peers: int = 5, limit: int = 20) -> dict:
    candidates = pool.loc[pool.benchmark_eligible & ~pool.is_daegu & pool.process_key.eq(row.process_key)].copy()
    if not row.benchmark_eligible or not row.process_key:
        return {'available': False, 'reason': '필수 지표 또는 품질 검토 조건 미충족', 'count': 0}
    for f in ['capacity_m3_day', 'inflow_m3_day', 'bod_load_kg_year']:
        candidates = candidates.loc[candidates[f].between(row[f] / 2, row[f] * 2)]
    count = len(candidates)
    if count < min_peers:
        return {'available': False, 'reason': f'동일 공법·규모·부하 조건을 만족하는 타 지역 시설 {count}개 (최소 {min_peers}개 필요)', 'count': count}
    distance = sum(np.log(candidates[f] / row[f]) ** 2 for f in
                   ['capacity_m3_day', 'inflow_m3_day', 'bod_load_kg_year']) ** .5
    candidates = candidates.assign(distance=distance).sort_values(['distance', 'facility_id']).head(limit)
    median = candidates.kwh_m3.median()
    return {'available': True, 'count': len(candidates), 'candidate_count': count,
            'median_kwh_m3': median, 'q25_kwh_m3': candidates.kwh_m3.quantile(.25),
            'q75_kwh_m3': candidates.kwh_m3.quantile(.75), 'ratio': row.kwh_m3 / median,
            'percentile': 100 * candidates.kwh_m3.le(row.kwh_m3).mean(),
            'peer_bod_removal_median': candidates.bod_removal_pct.median(),
            'peer_ids': candidates.facility_id.tolist(),
            'peers': candidates[['facility_id', 'region', 'name', 'kwh_m3', 'distance']].to_dict('records')}
