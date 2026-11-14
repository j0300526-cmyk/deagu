"""Conservative API validation: opdate + meter only; annual energy observations are untouched."""
from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

from .core import ROOT, RAW, PROCESSED, YEAR

SOURCE='https://www.data.go.kr/data/15157553/openapi.do'
METRICS={'TOC(mg/L)':'TOC','T-N(mg/L)':'T-N','T-P(mg/L)':'T-P','SS(mg/L)':'SS'}
DIMENSIONS=['opdate','ouId','gno','cno','qno','sno']


def analyze_hasu():
    folder=RAW/'hasu_api'
    manifest=folder/f'collection_{YEAR}.json'
    if not manifest.exists(): return {'available':False,'reason':'연간 API 원본 수집 전'}
    metadata=json.loads(manifest.read_text(encoding='utf-8'))
    if not metadata or any(not item.get('complete') for item in metadata):
        raise RuntimeError('운영 API 수집이 불완전합니다. 실패 날짜를 재수집한 뒤 분석을 실행하세요.')
    records=[]
    for meta in metadata:
        for page in range(1,(int(meta.get('totalCount') or 0)+999)//1000+1):
            p=folder/f'{meta["date"]}_page{page}.xml'
            if not p.exists():continue
            root=ET.fromstring(p.read_bytes())
            if root.findtext('.//resultCode')!='00':continue
            for item in root.findall('.//item'):
                row={c.tag:c.text for c in item}
                row['query_date']=meta['date'];row['source_file']=p.name
                records.append(row)
    d=pd.DataFrame(records)
    if not len(d):return {'available':False,'reason':'성공 응답의 관측 행 없음'}
    date_parse=pd.to_datetime(d.opdate,errors='coerce')
    d=d.loc[date_parse.dt.year.eq(YEAR)].copy()
    # Composite identifiers are used to distinguish processes, lines and columns with the same display text.
    duplicate=d.duplicated(DIMENSIONS,keep=False)
    duplicate_n=int(duplicate.sum())
    # Duplicate dimension records are quarantined rather than counted twice or silently averaged.
    clean=d.loc[~duplicate].copy()
    clean['value']=pd.to_numeric(clean.meter.astype(str).str.strip().str.replace(',','',regex=False),errors='coerce')
    q=clean.loc[clean.GDesc.eq('유입.방류수질') & clean.SDesc.eq('방류수') & clean.QDesc.isin(METRICS)].copy()
    q['metric']=q.QDesc.map(METRICS)
    q['unit']='mg/L'
    # Concentrations cannot be negative. Missing strings are not backfilled with BMeter or previous days.
    q.loc[q.value.lt(0),'value']=np.nan
    daily_dups=q.duplicated(['opdate','ouId','metric'],keep=False)
    ambiguous_daily_n=int(daily_dups.sum())
    q=q.loc[~daily_dups].copy()
    q['month']=pd.to_datetime(q.opdate).dt.strftime('%Y-%m')
    monthly=[];coverage=[]
    for (site,metric),group in q.groupby(['ouId','metric'],sort=True):
        v=group.value.dropna()
        coverage.append({'site':site,'metric':metric,'unit':'mg/L','record_days':group.opdate.nunique(),
                         'valid_days':len(v),'missing_or_absent_days':365-len(v),
                         'missing_pct':100*(365-len(v))/365,'annual_observed_mean':v.mean(),
                         'minimum':v.min(),'maximum':v.max()})
        for month in pd.period_range(f'{YEAR}-01',f'{YEAR}-12',freq='M'):
            dates=group.loc[group.month.eq(str(month))]
            good=dates.value.dropna()
            monthly.append({'site':site,'metric':metric,'unit':'mg/L','month':str(month),'calendar_days':month.days_in_month,
                            'valid_days':len(good),'mean':good.mean(),'min':good.min(),'max':good.max(),
                            'coverage_pct':100*len(good)/month.days_in_month})
    PROCESSED.mkdir(parents=True,exist_ok=True)
    d.to_csv(PROCESSED/f'hasu_operational_raw_{YEAR}.csv',index=False,encoding='utf-8-sig')
    q.to_csv(PROCESSED/f'hasu_effluent_daily_{YEAR}.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(monthly).to_csv(PROCESSED/f'hasu_effluent_monthly_{YEAR}.csv',index=False,encoding='utf-8-sig')
    dates=sorted(d.opdate.dropna().unique())
    offsets=(pd.to_datetime(d.query_date)-pd.to_datetime(d.opdate)).dt.days.value_counts().to_dict()
    electricity=clean.loc[clean.GDesc.str.contains('전기|전력',na=False)|clean.QDesc.str.contains('전력|kWh|kw/',case=False,na=False)]
    labels={'agoClass':'이전자료 유무 (미사용)','agoDay':'이전자료 일수 (미사용)','BMeter':'가동값 (정확한 의미 미확인·미사용)',
            'CDesc':'행명','cno':'행 ID','GDesc':'항목명','gno':'항목 ID','meter':'원 가동값 (단위는 QDesc 확인)',
            'opdate':'운영일 (관측일로 사용)','ouId':'처리장·사업소명','QDesc':'열명·원문 단위','qno':'열 ID',
            'SDesc':'계열명','sno':'계열 ID','reference':'추가 응답 필드 (공식 Swagger 설명 없음·미사용)'}
    column_quality=[{'column':col,'meaning':meaning,'blank_n':int(d[col].isna().sum()),
                     'blank_pct':100*d[col].isna().mean()} for col,meaning in labels.items() if col in d]
    out={
        'available':True,'year':YEAR,'source_url':SOURCE,'endpoint':'https://apis.data.go.kr/B554808/Hasu/svHasu',
        'request_days':len(metadata),'complete_request_days':sum(x.get('complete',False) for x in metadata),
        'raw_records':len(d),'operation_days':len(dates),'start_date':dates[0] if dates else None,'end_date':dates[-1] if dates else None,
        'source_sites':sorted(d.ouId.unique()),'query_operation_day_offsets':{str(k):int(v) for k,v in offsets.items()},
        'duplicate_dimension_records':duplicate_n,'ambiguous_daily_records':ambiguous_daily_n,
        'effluent_sites':sorted(q.ouId.unique()),'effluent_records':len(q),'valid_effluent_records':int(q.value.notna().sum()),
        'coverage':coverage,'monthly':monthly,'column_quality':column_quality,
        'electricity_labels':electricity[['ouId','GDesc','QDesc']].drop_duplicates().to_dict('records'),
        'model_included':False,'energy_comparable':False,'coordinates_available':False,
        'definition':'응답 opdate를 관측일로 사용. meter만 원 관측값으로 해석하고 BMeter는 의미 미확인으로 계산 제외. 방류수 농도 월평균은 유량 가중이 아닌 유효 일 관측값의 산술평균.',
        'limitations':[
            '조회일과 운영일이 다를 수 있어 응답 opdate를 기준으로 2025년만 선택했다.',
            '월평균은 유효한 날의 단순 평균이다. 결측일·미수록일을 0 또는 전일값으로 채우지 않았다.',
            '응답의 전력 항목은 북부 총인 공정의 총인전력량(kw/일)로 표기되어 전체 시설 kWh와 비교·합산하지 않았다.',
            '이 자료에는 공식 위경도·계통구매 전력·전 시설 일별 총전력 검증 근거가 없어 지도와 기존 연간 모델에 결합하지 않았다.',
            '사업소명은 API 원문 표기다. 시설 매칭과 법정 방류수 준수 판정은 수행하지 않았다.',
        ]}
    return out


def report_hasu(api):
    if not api.get('available'):return '# 운영 API 검증\n\n'+api.get('reason','자료 없음')
    def f(v):return '산출 불가' if v is None or pd.isna(v) else f'{v:.3f}'
    rows='\n'.join('| '+ ' | '.join([x['site'],x['metric'],str(x['valid_days']),str(x['record_days']),f"{x['missing_pct']:.1f}%",f(x['annual_observed_mean'])])+' |' for x in api['coverage'])
    limits='\n'.join('- '+x for x in api['limitations'])
    columns='\n'.join('| '+ ' | '.join([x['column'],x['meaning'],str(x['blank_n']),f"{x['blank_pct']:.2f}%"] )+' |' for x in api['column_quality'])
    return f'''# 대구 하수 처리 현황 API 검증 및 수질 보강

출처: [대구공공시설관리공단 하수 처리 현황 GW]({SOURCE}). 이용허락범위 제한 없음.
인증키는 gitignored `.env.local`의 HASU_SERVICE_KEY에서만 읽는다. 키·인증 포함 URL은 원본·보고서·웹 산출물에 저장하지 않는다.

## 실제 수집 범위

- 관측기간: {api['start_date']} ~ {api['end_date']}. 관측일 {api['operation_days']}개.
- 요청일 {api['request_days']}개 중 페이지 수·결과 건수 완전 확인 {api['complete_request_days']}개.
- 2025년 원본 관측 행 {api['raw_records']:,}개. 사업소 표기 {len(api['source_sites'])}개.
- 방류수 TOC·T-N·T-P·SS 선택 행 {api['effluent_records']:,}개, 유효 수치 {api['valid_effluent_records']:,}개.
- 복합 차원 중복 격리 {api['duplicate_dimension_records']}행. 같은 날·사업소·항목의 모호한 복수값 격리 {api['ambiguous_daily_records']}행.
- 조회일−관측일 오프셋(일): {api['query_operation_day_offsets']}.

2025년 1월 1일 관측은 2025년 1월 2일 조회, 12월 31일 관측은 2026년 1월 1일 조회에서 확보했다.
코드는 날짜를 일률 덮어쓰지 않고 모든 응답의 opdate를 확인한다. 요청 파라미터와 응답 해시는 `data/raw/hasu_api/collection_2025.json`에 보존한다.

## 집계 방법

{api['definition']}

원본의 가동값 문자열 '-'·빈값은 결측이다. '0.' 등 실제 숫자 표기는 수치로 읽는다.
숫자가 아닌 표기와 음수 농도를 유효값으로 쓰지 않는다. 결측률의 분모는 사업소·항목별 365일이다.
연간 관측 평균은 유효 일수에 대한 단순 평균이며 전국 연간 통계의 평균과 교체하지 않는다.

## 원본 응답 필드와 공란률

아래 공란률은 XML의 비어 있는 값만 센다. 행·열·계열 설명의 '-'는 해당없음 표기일 수 있으므로
수치 meter의 결측 판단과 구분한다. reference는 실제 응답에 있지만 문서화된 스키마에는 설명이 없어 해석하지 않는다.

| 필드 | 원문 의미·사용 범위 | 공란 수 | 공란률 |
| --- | --- | --- | --- |
{columns}

## 방류수 농도 관측 범위

| API 사업소 표기 | 방류 항목 | 유효 일수 | 수록 일수 | 결측·미수록률 (365일 기준) | 유효일 농도 평균 mg/L |
| --- | --- | --- | --- | --- | --- |
{rows}

## 해석과 한계

{limits}

## 재현

```powershell
python scripts/collect_hasu.py --year 2025
python -m analysis.pipeline
```

수집은 원본 캐시를 재사용한다. 원본 XML·공식 Swagger는 data/raw/hasu_api에 보존한다.
가공 데이터: hasu_operational_raw_2025.csv, hasu_effluent_daily_2025.csv, hasu_effluent_monthly_2025.csv.
웹에는 인증키 없이 사전 계산한 월별 결과만 배포한다. 단위 확인이 안 된 전력·PH 지표는 최종 수치 분석에서 제외한다.
'''
