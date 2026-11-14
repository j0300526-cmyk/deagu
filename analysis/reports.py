"""Reports are generated from the same values consumed by the website."""
from pathlib import Path
import shutil

from .core import ROOT, FIELDS, SOURCE_URL, CATALOG_URL, GIR_URL
from .hasu import report_hasu


def table(headers, rows):
    def cell(x): return str(x).replace('|', '\\|').replace('\n', ' ')
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---']*len(headers)) + ' |'] +
                     ['| ' + ' | '.join(cell(x) for x in row) + ' |' for row in rows])


def write_reports(data, manifest):
    q = data['quality']; dg = data['summary']['daegu']; ns = data['summary']['national']; m = data['model']
    reports = {}
    reports['DATA_SOURCES.md'] = f'''# 공공데이터 출처 및 활용 내역

확인일: 2026-11-13 (Asia/Seoul). 주 분석 관측연도: 2025년. 전년 비교: 2024년.

{table(['출처','자료·기준연도','활용','이용 조건'], [
['[한국환경공단 공공하수처리시설 현황]('+SOURCE_URL+')','CSV 파일명 20251231 / 4,556행·60열','전국·대구 수질, 전력, 공법·부하 비교','포털: 이용허락범위 제한 없음; 출처 명시'],
['[환경부 하수도통계 공식 자료목록]('+CATALOG_URL+')','2025 통계, 2026-07-31 게시; 2024 통계, 2025-11-10 게시','CSV 관측연도·단위 검증; 2024 비교; 2025 슬러지·재이용 총량','원본 저작권·이용조건 확인 필요. 사실 수치·가공 결과 출처 명시'],
['[한국환경공단 하수도정보](https://www.data.go.kr/data/15137402/fileData.do)','제공된 9개 CSV, 각 행의 년도 기준','지역·연도 통계 별도 프로파일. 관측연도·집계수준이 달라 시설 모델에 결합하지 않음','포털: 이용허락범위 제한 없음'],
['[GIR 2025 승인 계수]('+GIR_URL+')','2025-12-18 공표 / 2021–2023 평균','소비단 0.4330 tCO₂eq/MWh. 2023 단년도 0.4173과 구분','공식 공표 수치 인용; PDF 별도 개방 라이선스 미확인'],
['[GIR 2024 승인 계수](https://www.gir.go.kr/home/board/read.do?boardMasterId=2&boardId=82&menuId=36)','2025-03-31 공표 / 2020–2022 평균','2024 CSV의 참고 환산량 0.4541 tCO₂eq/MWh. 연도별 탄소 추이는 제시하지 않음','공식 공표 수치 인용; PDF 별도 개방 라이선스 미확인'],
['[대구 하수관거 및 관로 현황](https://www.data.go.kr/data/3045606/fileData.do)','20260101 파일 / 89행','관로 보강자료 보존·프로파일; 시설 좌표로 전환하지 않음','포털: 이용허락범위 제한 없음'],
['[Statistics Korea SGIS 기반 행정경계](https://github.com/DevMinGeonPark/mapcn-kr/blob/main/LICENSE-DATA)','2026 행정리·읍면동 경계 / mapcn-kr 고정 버전','공개 주소의 행정구역 내부 대표점. 시설 부지 좌표 아님','SGIS / mapcn-kr, CC BY 4.0 출처표시'],
['[OpenStreetMap](https://www.openstreetmap.org/copyright)','현재 지도 배경·동/도로 객체','9개 시설의 동 또는 도로 대표점. 시설 부지 좌표 아님','© OpenStreetMap contributors / ODbL']])}

## 원본 확보 및 연도 확정

기존 제공 파일은 원래 위치에 두고 `data/raw/`에 그대로 복사했다. 포털 다운로드 엔드포인트에서
전국 CSV를 다시 다운로드한 파일은 `facilities_portal_download.csv`이다. 기존 CSV와 SHA-256이 일치했다.
메타데이터의 시간범위(2015–2024)와 파일명(20251231)이 서로 일관되지 않아, 파일명만으로 관측연도를 정하지 않았다.
공식 2025 XLSX의 개별 시설행과 CSV의 13개 필드(시도·시설명·주소·용량·유량·BOD·TOC·T-N·T-P·공법·전력)를
{q['rows']:,}행 전수 대조해 모두 일치함을 확인했다. 비교 코드: `analysis/core.py: verify_2025`.
근거: `data/processed/year_verification.json`, 원본 헤더·본문: `statistics_2025_catalog.xlsx`.

## 다시 다운로드하는 방법

`python scripts/acquire.py`는 로그인 없이 공개된 파일만 다운로드한다. 현재 확보 파일로 분석은 오프라인 실행 가능하다.
접근이 막히거나 CAPTCHA가 나오면 우회하지 말고 다음을 수행한다.

1. 공공데이터포털 3073222에서 다운로드 → `data/raw/facilities_portal_download.csv`로 보관.
2. 위 환경부 공식 자료목록에서 “2025 하수도통계(최종).xlsx”, “2024 하수도통계(최종)★.xlsx” 다운로드 → 각각 `statistics_2025_catalog.xlsx`, `statistics_2024_catalog.xlsx`.
3. GIR 게시글 86의 PDF 다운로드 → `data/raw/gir_2025.pdf`. 게시글 82의 PDF는 `gir_2024.pdf`.
4. 15137402에서 연결되는 국가하수도정보시스템의 통계별 CSV는 기존 `data/raw/한국환경공단_하수도정보/`에 보존. 재수집 시 기준연도·단위를 함께 저장.
5. 추정 지도점은 `python scripts/estimate_facility_locations.py`로 행정리 경계 또는 OSM 동·도로 대표점에서 재생성. `data/coordinates_estimated.csv`에 위치 유형과 출처를 기록한다. 공식 시설 좌표가 확보되면 `data/coordinates.csv`에 근거 URL·verified=true로 별도 입력한다.

## 표준 컬럼과 단위

시설용량·유입·방류량은 공식 XLSX의 `6. 공공하수처리시설(전체)` 표 머리글에 m³/일로 표시된다.
유입량은 연간 적산량이 아닌 일평균 규모 지표로 사용하고 2025년 365일, 2024년 366일을 곱해 연간 환산한다.
연간 유량과 농도를 곱한 BOD 부하는 연평균의 곱으로 근사한 값이며 적산 실측 오염부하와 다르다.
재이용 표의 연간 하수처리량은 방류량과 대응하는 천톤/년 지표로, 유입량 분모와 혼용하지 않는다.

{table(['표준 컬럼','원본 의미','단위'], [(k,v[1],v[2] or '문자열') for k,v in FIELDS.items()])}

원본 60개 컬럼 전체 결측률·사용 여부·단위는 DATA_QUALITY_REPORT.md 및 `data/processed/data_quality.json`에 기록했다.
전 파일 해시는 `data/processed/source_manifest.json`에 있다. SHA는 무결성 근거이며 데이터 내용의 정확성을 보증하지 않는다.
'''
    reports['DATA_QUALITY_REPORT.md'] = f'''# 데이터 품질 보고서

2025년 전국 {q['rows']:,}개, 대구 {q['daegu_rows']}개 시설. 인코딩: {q['encoding']}.
관측값의 결측을 0으로 채우지 않았다. 모델 입력의 결측만 훈련 fold 내 중앙값으로 대치한다.
시설 원본·가공 CSV와 JSON은 같은 파이프라인에서 생성한다.

## 검증 결과

- CSV와 2025 공식 XLSX: 13개 필드 × {q['rows']:,}행 전수 일치. 포털 메타데이터의 시간범위 오류 가능성을 별도 기록.
- 주소 포함 복합 식별자 중복: {q['duplicates_composite']}건. 시도·구군·시설명만 같아 주소로 구분해야 하는 행: {q['duplicate_region_district_name']}개.
- 품질 검토 플래그가 있는 전국 시설: {q['flagged_n']}개. 전국 비교·모델 적격: {q['benchmark_n']:,}개, 대구 적격: {q['daegu_benchmark_n']}개.
- 전국 원단위 계산 가능: {ns['intensity_valid_n']:,}개. 전력 총계는 양의 전력 기록을 합산한다. 결측이 존재하면 전국 전체 실측 총계가 아닌 확보 기록 합계이다.
- 유입량 가중 평균 {ns['weighted_kwh_m3']:.4f}, 전국 품질검토 통과 시설의 원단위 중앙값은 JSON으로 확인 가능. 원자료 총계에는 플래그 시설을 보존한다.
- 지도 위치 {q['coordinates_n']}개: 공식 검증 {q['coordinates_verified_n']}개, 주소 기반 추정 {q['coordinates_estimated_n']}개. 추정점은 시설 부지 좌표가 아닌 행정구역·동·도로 대표점이다.
- {q['previous_year_note']}
- 전년 비교는 시도·구군·정규화 시설명 유일 일치 + 공백 정규화 주소 일치 조건을 사용한다. 대구 {len(data['trends'])}개 연결. 행정구역 변화·개명 시설을 임의 연결하지 않는다.

## 품질 검토 규칙과 제외 수

{table(['사유','행 수 (사유 중복 가능)'], q['flags'].items())}

전력원단위 0.02 미만 또는 10 초과 kWh/m³, 유입/시설용량 5% 미만 또는 250% 초과는
측정 범위·운전상태 확인을 위한 사전 검토 플래그이다. 물리적으로 불가능하거나 오류라고 단정하지 않는다.
이 임계값은 공인 효율 기준이 아닌 분석 운영 규칙이다. 목표변수 극단값 선별에 따른 선택 편향이 있으므로
모델 성능은 이 적격 표본 범위에만 적용한다. 원자료를 제거·수정하지 않고 원본과 플래그를 함께 제공한다.
0 또는 음수 전력은 시설 효율이 0이라고 해석하지 않는다. BOD 유입≤0, 방류<0 또는 유입<방류는 제거율을 산출하지 않는다.

## 원본 전 컬럼 결측률

{table(['원본 컬럼','표준 컬럼','단위','결측 수','결측 %','숫자 변환 실패'], [(c['original'],c['standard'] or '미사용',c['unit'],c['missing_n'],f"{c['missing_pct']:.2f}",c['parse_failure_n'] if c['parse_failure_n'] is not None else '해당 없음') for c in q['columns']])}

## 추가 파일 프로파일

{table(['파일','행','열','인코딩','최소년도','최대년도'], [(f['file'],f['rows'],f['columns'],f['encoding'],f['year_min'] or '연도열 없음',f['year_max'] or '연도열 없음') for f in q['files']])}

추가 CSV의 컬럼별 결측 수·결측률은 `data/processed/data_quality.json: files[].missing`에 보관했다.
일부 지역 통계는 최신 시설 자료와 연도·집계수준이 달라 모델에 사용하지 않는다. 추가 파일의 미확인 단위는 임의 변환하지 않았다.
공식 2025 슬러지·재이용 XLSX 지역 총량은 별도 부록으로 제공하고 시설에 비례 배분하지 않는다.

## 산정 범위 및 남은 한계

일평균 유량 × 연간 일수는 연간 환산량이며 일별 운영·우천 변동을 재구성하지 못한다.
평균 유량과 평균 농도의 곱은 평균 질량부하와 정확히 같지 않다. BOD 제거율은 농도비 기반이고
BOD 제거 근사질량은 유입·방류 각각의 유량을 사용하는 질량수지 기반이다.
슬러지 반입처리, 연계처리, 방류수 기준, 공정 범위, 계통구매 전력량에 대한 현장 검증이 추가로 필요하다.
'''
    facility_rows = []
    for f in sorted(data['facilities'],key=lambda x: x['kwh_m3'] if x['kwh_m3'] is not None else float('inf')):
        p = data['peers'][f['facility_id']]
        fmt=lambda v,n=3: '산출 불가' if v is None else f'{v:.{n}f}'
        facility_rows.append([f['name'],f['district'],f['method'],fmt(f['electricity_kwh']/1e6),fmt(f['kwh_m3']),fmt(f['kwh_kg_bod']),fmt(f['bod_removal_pct'],2),f"{p['ratio']:.2f}배 ({p['count']}개)" if p['available'] else p['reason']])
    insights='\n\n'.join(f"## {i+1}. {x['title']}\n\n**{x['value']} {x['unit']}**\n\n{x['finding']}\n\n- 비교: {x['comparison']}\n- 정책 제언: {x['policy']}\n- 한계: {x['limitation']}\n- 출처: {x['source']} / {x['year']}년" for i,x in enumerate(data['insights']))
    reports['ANALYSIS_REPORT.md'] = f'''# 대구 하수처리시설의 숨은 탄소격차

공공데이터와 AI를 활용한 하수처리시설의 수질 정화 성능·에너지 효율·탄소배출 특성 분석

주 관측연도 2025년. 전국 {ns['n']:,}개, 대구 {dg['n']}개. [주 출처]({SOURCE_URL}), [연도·단위 검증 원본]({CATALOG_URL}).

## 연구 설계

분석은 지역 총량 → 규모별 구성 → 동일 공법·유사 부하 비교 → 설명 모델 → 가정 시나리오 순서다.
전국 전체와 대구 전체 평균 비교는 구성 차이가 남는 기술통계이다. 지역 운영성과를 판단하려면 유사 시설 비교가 필요하다.
유사 시설은 대구를 제외한 전국에서 공법 조합이 같고, 시설용량·일평균 유입량·유입 BOD 연간 부하가 각각
해당 시설의 0.5–2배인 시설을 고른다. 세 변수의 로그 비율 거리로 최대 20개를 사용하며 5개 미만이면 비교를 비활성화한다.
각 비교집단의 시설 ID·이름·원단위·거리를 `public/data/analysis.json: peers`에 공개했다.

## 재현 가능한 핵심 식

- 연간 환산 유입량(m³/년) = 일평균 유입량(m³/일) × 연도 일수(2025:365, 2024:366).
- 전력 원단위(kWh/m³) = 연간 전력(kWh/년) / 연간 환산 유입량(m³/년).
- BOD 농도 제거율(%) = (유입 BOD − 방류 BOD) / 유입 BOD × 100.
- 연간 BOD 제거 근사질량(kg/년) = (Qin연간 × Cin − Qout연간 × Cout) / 1,000. 농도 단위 mg/L.
- BOD 제거당 전력(kWh/kg-BOD) = 연간 전력 / 연간 BOD 제거 근사질량.
- 표준화 전력 간접배출 추정(tCO₂eq/년) = 연간 총전력(kWh) / 1,000 × 0.4330(tCO₂eq/MWh).

질량은 유입·방류 유량을 각각 사용한다. 원자료 CO₂ 지표(kgCO₂/m³)는 다른 산정범위일 수 있어 별도 열로 보존한다.
새로 계산한 간접배출량은 원자료 CO₂ 값이나 시설 전체 온실가스 배출량과 합치거나 대체하지 않는다.
계수는 2025 승인·2021–2023 평균·소비단이며 2025년 전력믹스를 직접 측정한 연도 계수가 아니다.

{insights}

## 대구 시설별 결과 (2025년)

{table(['시설','구군','처리공법','전력 GWh/년','kWh/m³','kWh/kg-BOD','BOD 제거율 %','유사시설 대비'],facility_rows)}

## 규모·수질·공법의 관계

전국 적격 표본에서 시설용량과 연간 전력의 Spearman 상관계수는 {data['correlations']['electricity_kwh']['capacity_m3_day']:.3f},
BOD 제거율과 kWh/m³의 Spearman 상관계수는 {data['correlations']['kwh_m3']['bod_removal_pct']:.3f}이다.
상관은 시설 규모·공법·지역 조건이 혼재된 단면의 연관성이며 인과효과가 아니다.
공법별 값은 n≥5인 조합만 공개하며, 설계 구성·규모·방류 기준을 통제한 공법의 인과 비교가 아니다.

{table(['시설 규모 (m³/일)','전국 적격 n','대구 적격 n','전국 중앙값 kWh/m³','대구 중앙값 kWh/m³'],[(x['scale'],x['national_n'],x['daegu_n'],f"{x['national_median']:.3f}" if x['national_median'] is not None else '없음',f"{x['daegu_median']:.3f}" if x['daegu_median'] is not None else '없음') for x in data['scale_comparison']])}

## 연도 비교와 보강자료

2024–2025 동일 시설로 확인되는 대구 {len(data['trends'])}개를 연결했다. 전력과 원단위를 각각 제공한다.
연도별 원단위 분모는 해당 연도의 일수를 사용한다. 에너지 산정 경계·시설 증설·공법 변경이 있을 수 있으므로 변화를 운영개선 효과로 단정하지 않는다.
전국 2024 전체와 2025 전체의 표본 수가 달라 전국 총량 증감률을 제시하지 않는다.
2025년 대구 하수찌꺼기 발생량은 {data['supplementary']['sludge']['generated_t_year']:,.1f} 톤/년(탈수기준),
하수처리수 재이용량은 {data['supplementary']['reuse']['reused_thousand_t_year']:,.1f} 천톤/년이다.
지역 총량이며 개별 시설 모델의 입력으로 배분하지 않았다.

## 실행 제안

1. 유사시설 대비 원단위가 높은 시설은 수질·연계처리·슬러지·계측범위를 확인하는 진단 목록으로만 사용한다.
2. 송풍·펌핑·고도처리·슬러지 공정별 전력계측과 우천/건천 유량·농도를 수집해 원인 가설을 검증한다.
3. 방류 BOD·TOC·T-N·T-P 및 법적 기준의 유지 여부를 확인한 실증에서 절감량·투자비·회수기간을 평가한다.
4. 실증 전·후 비교에는 계절·강우·부하 변화를 통제하고, AI 예측 또는 타 시설 중앙값을 절감목표로 쓰지 않는다.

AI 결과의 정확도와 적용 한계는 MODEL_EVALUATION.md 참조.
'''
    if m['available']:
        metrics_rows=[]
        for e in m['evaluations']:
            for sample,key in [('타 지역 5-fold OOF','cv'),('대구 전체 독립평가','daegu')]:
                if e[key]:
                    z=e[key]; metrics_rows.append([e['name'],sample,z['n'],f"{z['mae']:.4f}",f"{z['rmse']:.4f}",f"{z['r2']:.4f}"])
        reports['MODEL_EVALUATION.md'] = f'''# AI 모델 평가

목표변수: 2025년 kWh/m³ (일평균 유입량을 연간 환산한 분모). 적용 가능 표본: 품질 검토 조건 통과 시설만.
학습: 대구를 제외한 {m['train_n']:,}개. 대구 독립평가 {m['daegu_n']}개. 전체 제외 {m['excluded_n']}개.

## 누수 방지 및 비교

동일한 입력·동일한 분할에서 Ridge 선형 기준모델, RandomForest, XGBoost를 비교했다.
Ridge는 alpha=10, RandomForest는 트리 160개, min_samples_leaf=5, max_depth=18, seed=42이다.
XGBoost는 300개 트리, learning_rate=0.05, max_depth=4, min_child_weight=5, subsample=0.8,
colsample_bytree=0.9, reg_alpha=0.1, reg_lambda=5, tree_method=hist, n_jobs=4, seed=42로 고정했다.
목적함수 reg:squarederror를 로그 목표에 적용했다. 대구 점수에 맞춘 튜닝·조기종료를 하지 않았다.
전력 원단위의 오른쪽 꼬리를 고려해 목표값에 log를 적용하고 exp로 역변환했다. 보정하지 않은 기하학적 중심 추정으로 산술평균 편향이 있을 수 있다.

입력: log(1+시설용량), log(1+유입량), 유입 BOD·T-N·T-P, 가동기간, 공법 조합.
전력량·에너지사용량·에너지자립율·CO₂·BOD 제거당 전력 등 목표변수 직접 파생값은 입력에서 제외했다.
방류농도·제거율도 이번 모델에서는 제외했다. 연평균 유입조건이 알려진 상태의 조건부 설명 모델이므로
연도 시작 전에 사용할 수 있는 예측이라고 주장하지 않는다.

타 지역 5-fold GroupKFold(시도·구군·시설명 그룹). 같은 이름·행정구역의 다른 주소 시설도 같은 fold에 둔다.
대치·표준화·희소 공법 묶기·원핫 인코딩은 각 훈련 fold 안에서만 적합했다.
모델 선택 기준은 타 지역 OOF MAE이며 대구 점수로 선택하거나 튜닝하지 않았다.
선택 모델: **{m['selected']}**. 세 알고리즘을 모두 공개하며 복잡한 모델이 반드시 우수하다고 가정하지 않는다.
분할 근거: `data/processed/model_fold_assignment.csv`. 전체 OOF 예측은 `model_oof_predictions.csv`에 보관했다.
OOF는 모델 선택에도 사용했으므로 선택 모델의 CV 성능에는 선택 낙관성이 남을 수 있다. 대구 점수는 선택에 사용하지 않는다.

## 성능

{table(['모델','평가 범위','n','MAE (kWh/m³)','RMSE (kWh/m³)','R²'],metrics_rows)}

R²가 낮거나 음수이면 이 표본의 분산을 충분히 설명하지 못한다. 대구 평가 표본은 작아 오차 추정이 불안정할 수 있다.
XGBoost와 Ridge의 OOF MAE 차이는 작으며 유의성 검정을 수행하지 않아 통계적 우월성을 주장하지 않는다.
이번 대구 독립평가의 MAE는 RandomForest가 XGBoost보다 낮다. 선택 기준과 지역 일반화 결과를 구분해 읽어야 한다.
각 fold별 성능은 `data/processed/model_results.json`에 포함했다. 예측·실측은 `daegu_predictions.csv`.
임계값으로 원단위 극단값을 제외한 조건부 성능이며 전체 시설·미래 연도로 일반화하지 않는다.

## 변수 중요도

타 지역 첫 fold 훈련자료로 적합한 선택 모델 **{m['selected']}**에서 독립 검증 {m['importance_n']}개에 입력 컬럼을 8회 섞었다.
섞었을 때 증가한 MAE의 평균·표준편차를 보고한다. 음수는 안정적인 설명 기여가 확인되지 않음을 뜻한다.

{table(['변수','MAE 증가 평균 (kWh/m³)','표준편차'],[(x['feature'],f"{x['mean']:.5f}",f"{x['std']:.5f}") for x in m['importance']])}

상관된 입력은 중요도를 나눠 가질 수 있다. 중요도는 인과 기여나 절감률을 뜻하지 않는다.
잔차가 큰 시설은 누락된 운영조건·측정범위·자료오류 점검 대상으로 제시하며 비효율 확정·최적전력·달성가능 목표로 표현하지 않는다.
모델은 전력 절감 시뮬레이터에 사용하지 않는다. 시뮬레이터는 관측 전력량 × 사용자가 정한 가정 절감률이다.
'''
        s = m['shap']
        if s['available']:
            reports['MODEL_EVALUATION.md'] += f'''
## 실제 XGBoost Tree SHAP

설명 모델은 **XGBoost**이다. CV 선택 모델 **{m['selected']}**과 구분한다.
패키지: XGBoost {s['versions']['xgboost']}, SHAP {s['versions']['shap']}.
`shap.TreeExplainer(model_output="raw", feature_perturbation="interventional")`를 사용해
`approximate=False`, `check_additivity=True`로 실제 값을 계산했다. 대구 제외 훈련 시설에서
seed=42로 추출한 {s['background_n']}개만 배경자료로 사용했다. 배경 ID도 JSON에 공개했다.
대구 {s['n']}개 시설의 예측 설명이며 전국 대표 중요도·모델 성능 점수로 해석하지 않는다.

설명 척도는 **자연로그 log(kWh/m³)**이다. 회귀기가 로그 목표를 학습했기 때문에 raw 출력을 설명한다.
기준값 {s['base_value']:.8f}는 배경자료에 대한 평균 로그 예측이며 exp(기준값)={s['baseline_prediction']:.6f} kWh/m³이다.
실제 관측 평균이나 배경 예측 원단위의 산술평균과 구분한다.

`예측 로그 원단위 = 기준값 + Σ SHAP 기여도`

`예측 원단위 (kWh/m³) = exp(기준값 + Σ SHAP 기여도)`

양수 기여도는 기준 예측 대비 상승 방향, 음수는 하락 방향이다. kWh/m³에 직접 더할 수 없다.
각 시설의 복원 합산값과 XGBoost 출력 최대 절대 오차는 {s['max_additivity_error']:.3g} (로그 척도)이며
모든 시설에 대해 로그 출력 및 exp 역변환 일치 검사를 통과해야 분석이 완료된다.

{table(['순위','입력 변수','대구 평균 절대 SHAP (로그 척도)'], [(x['rank'], x['feature'], f"{x['mean_abs']:.6f}") for x in s['importance']])}

전처리 후 원핫 공법 열들의 부호 있는 기여도를 시설별로 합산해 원래 공법 변수로 되돌린 다음,
시설별 절댓값의 평균으로 중요도를 계산했다. 개별 원핫의 절댓값 합이나 별도의 그룹 Shapley 값이 아니다.
용량·유입량의 log(1+x)와 나머지 원래 입력값도 시설별 기여도에 함께 제공한다. 결측 입력은 JSON null로
표시되며 모델 내부에서 훈련 중앙값·최빈값으로 대치한다. 대구 관측값을 대치 배경이나 훈련에 쓰지 않는다.

interventional은 상관된 입력의 의존성을 깨는 배경 가정이다. 용량·유입량의 강한 상관과 원핫 범주 사이의
의존성 때문에 비현실적인 특성 조합이 설명에 영향을 줄 수 있고, 배경표본 변경 시 기여도도 달라질 수 있다.
이 분석의 SHAP는 인과효과·운영 조절량·절감 가능량을 추정하지 않는다. 예측 오차나 잔차의 원인 설명도 아니다.

재현 파일: `data/processed/xgboost_shap.json` (시설별 부호·입력값·순위·기준값·예측값),
`data/processed/model_results.json`, `data/processed/model_oof_predictions.csv`.
공식 구현 근거: [SHAP TreeExplainer](https://shap.readthedocs.io/en/latest/generated/shap.TreeExplainer.html),
[XGBoost Python API](https://xgboost.readthedocs.io/en/latest/python/python_api.html). 확인일 2026-11-13.
'''
    else:
        reports['MODEL_EVALUATION.md'] = '# AI 모델 평가\n\n학습 비활성: ' + m['reason']
    reports['AI_PROMPT_LOG.md'] = '''# AI 프롬프트 활용 내역서 초안

작성일 2026-11-13. 공모전 공식 양식·분량·필수 항목은 제공되지 않아 이 문서는 전사 가능한 초안이다.
실제 대화·실행 기록은 사용자가 원 대화에서 보관해야 한다. 아래는 문구의 요약이며 존재하지 않는 추가 대화를 만들지 않았다.

| 구분 | 사용 도구·입력 요약 | 활용 결과·검증 |
| --- | --- | --- |
| 최초 사용자 지시 | Codex / “DAEGU CARBON LAB”, 대구 하수처리시설의 에너지·수질·탄소 공공데이터 분석, 누수 방지 AI, React 대시보드, 가상 데이터 금지 | 데이터 접근→검증→Python→모델→JSON→6페이지→빌드→보고서 순서로 구현 |
| 자료 조사 | 공식 data.go.kr, 환경부 하수도통계, GIR에 대한 웹 열람·공개 파일 다운로드 | 출처 HTML·원본·파일 해시를 보존. 메타데이터 연도와 파일명의 충돌을 공식 통계 전수 대조로 해결 |
| 코드 생성 | 위 요구사항과 실제 파일 스키마를 문맥으로 전처리·통계·모델·웹 코드 작성 | 분석 파이프라인 재실행, 계산식·연도·표본·누수 검증 테스트와 프런트엔드 빌드 수행 |
| 결과 서술 | 실제 실행으로 생성한 통계·모델 성능을 근거로 정책 시사점 초안 작성 | 수치·표는 분석 JSON과 같은 코드에서 생성. 인과·최적 전력·실증 감축 주장은 제외 |
| XGBoost·SHAP 재분석 | 실제 사용자 요청: “XGBoost 모델·SHAP 분석 GPT-6 Astra로 다시 해봐”. GPT-6 Astra 분석 에이전트가 구현·실행 | 기존 2025년 원본과 동일한 타 지역 GroupKFold에 XGBoost 추가. 실제 TreeExplainer, 대구 제외 배경자료, 로그 척도 합산 검증. 대구 점수로 모델 선택·튜닝하지 않음 |

AI는 수집·분석 코드 작성과 서술을 보조했다. 원본 관측값을 AI로 생성하거나 결측 관측값을 사실처럼 보완하지 않았다.
사람의 최종 검토가 필요한 항목: 참가 자격·공식 제출양식·데이터 사용조건·시설별 운영 경계·현장 실증 타당성.
제출 전 실제 사용 모델명·사용일시·원문 프롬프트·수정 이력·본인 검증 내역을 공식 양식에 대조해 기재한다.
'''
    reports['PUBLIC_DATA_USAGE.md'] = '''# 공공데이터 활용 내역서 초안

작품명: 대구 하수처리시설의 숨은 탄소격차

| 활용 데이터 | 제공기관 | 활용 범위 | 재현 근거 |
| --- | --- | --- | --- |
| 공공하수처리시설 현황 (3073222) | 한국환경공단 | 전국 시설 수질·전력·부하·공법과 대구 비교 | 원본 CSV, year_verification.json, national_2025.csv |
| 2024·2025 하수도통계 | 환경부(현 기후에너지환경부) | 연도·단위 전수 대조, 동일 시설 변화, 슬러지·재이용 보강 | 공식 XLSX, source_manifest.json, analysis/core.py |
| 하수도정보 (15137402) | 한국환경공단 | 제공 통계별 보존·결측·연도 프로파일 | data_quality.json. 시설 모델 미결합 |
| 국가 온실가스 전력배출계수 | 온실가스종합정보센터 | 공식 소비단 CO₂eq 계수에 의한 표준화 추정·가정 시나리오 | gir_2025.pdf, ANALYSIS_REPORT.md |
| 하수관거 및 관로 현황 (3045606) | 대구공공시설관리공단 | 관로 보강 자료 보존·프로파일 | 원본 CSV, data_quality.json. 지도 좌표로 사용하지 않음 |

개별 URL·라이선스·기준연도·파일 해시는 DATA_SOURCES.md와 data/processed/source_manifest.json 참조.
이 문서는 공식 양식의 필드·분량·권리 확인 요구사항을 대체하지 않는다.
'''
    reports['README.md'] = f'''# DAEGU CARBON LAB

## 대구 하수처리시설의 숨은 탄소격차

2026 대구광역시 기후·환경·탄소중립 공공데이터 AI 활용대회 부문 2 출품용 분석 프로젝트.
전국 {ns['n']:,}개·대구 {dg['n']}개 시설의 실제 2025년 공공데이터를 사용한다.
React + TypeScript + Vite + Tailwind + Recharts + Leaflet, Python/Pandas/NumPy/Scikit-learn/GeoPandas/XGBoost/SHAP.

## 실행

Python 3.14, Node 24에서 검증했다. 패키지 가용성이 다른 환경은 requirements 설치 결과를 확인한다.
API 수집 전에 `.env.example`을 `.env.local`로 복사하고 개인 `HASU_SERVICE_KEY`를 입력한다.

```powershell
python -m venv .venv
.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
npm ci
python scripts/acquire.py
python scripts/collect_hasu.py --year 2025
python -m analysis.pipeline
npm run dev
```

브라우저에서 Vite가 출력하는 주소(기본 http://127.0.0.1:5173)를 연다.

```powershell
python -m pytest -q
npm run test:render
npm run build
npm run preview
```

Vercel: 프레임워크 Vite, 빌드 `npm run build`, 출력 `dist`. `vercel.json` 포함.
사전 생성된 JSON이 저장되어 있으므로 배포 빌드 중 Python·API 키·서버 DB는 필요하지 않다.
공개 사이트: https://deagu-phi.vercel.app. SPA 내부 화면은 해시 경로를 사용해 새로고침을 지원한다.

## 분석 재현 및 파일

- `scripts/acquire.py`: 공개 원본 재수집. 다운로드 실패·로그인·CAPTCHA는 안내하고 원본을 생성하지 않음.
- `analysis/core.py`: 인코딩·컬럼·단위·연도 검증, 전처리·지표·유사시설 선정.
- `analysis/model.py`: 타 지역 시설 그룹 5-fold와 대구 독립평가, Ridge·RandomForest·XGBoost, 선택 모델 Permutation Importance, XGBoost Tree SHAP.
- `data/processed/model_oof_predictions.csv`: 세 모델의 전체 타 지역 OOF 예측·fold·시설 ID. 성능 재계산 가능.
- `data/processed/xgboost_shap.json`: 대구 시설별 부호 있는 로그 척도 기여도·입력·기준값·예측 및 평균 절대 중요도. exp(기준값+합)=예측 원단위 검증.
- `analysis/pipeline.py`: 전체 파이프라인. 네트워크 호출 없이 원본에서 CSV·JSON·보고서 생성.
- `data/raw/`: 기존 제공 파일과 공개 원본, 출처 HTML·공식 계수 PDF.
- `data/processed/`: 전국·대구 CSV, 품질·검증·모델·파일해시, 빈 GeoJSON.
- `public/data/analysis.json`: 웹 화면의 유일한 분석 결과 입력. 생성 코드 외에 수동 수치를 삽입하지 않음.
- `src/`: 6개 분석 화면. 검색·규모·공법 필터, 시설 상세, 비교·가정 시나리오, CSV·보고서 다운로드.
- `tests/`: 실제 데이터에 대한 연도 대조·계산식·보존·표본·누수·시나리오 검증.

문서: [데이터 출처](DATA_SOURCES.md), [품질](DATA_QUALITY_REPORT.md), [분석·정책](ANALYSIS_REPORT.md),
[모델](MODEL_EVALUATION.md), [AI 활용](AI_PROMPT_LOG.md), [공공데이터 활용](PUBLIC_DATA_USAGE.md).
이 README와 결과 보고서는 분석 실행 시 실제 계산 결과에서 다시 생성된다.
검증 범위와 브라우저 검증의 제한은 [실행·검증 기록](VERIFICATION_REPORT.md)에 별도 기록했다.

이 Windows OneDrive 폴더에서 출력 디렉터리 자동 정리 중 native 충돌을 관찰해 Vite의
`emptyOutDir: false`를 적용했다. 재빌드 시 이전 해시 자산이 남을 수 있으나 최신 index.html은
최신 자산을 참조한다. Vercel 새 빌드 디렉터리에는 잔여 파일이 없다.

## 기능과 해석

Overview, Facility Map, Energy Benchmark, AI Insights, Carbon Simulator, Policy Insights의 6개 화면.
전국 비교와 대구 분석, 관측·근사·AI·가정 시나리오를 구분한다. 모든 결과는 2025년이며 전년 비교만 2024년을 별도 표시한다.
지도는 2025년 시설 주소를 2026년 SGIS 기반 행정경계의 구역 내부 대표점 또는 OSM 동·도로 객체에 연결한
추정 위치를 표시한다. 이 점은 시설 필지·건물 좌표가 아니다. 공식 좌표는 아직 {q['coordinates_verified_n']}개이며,
공식 좌표·근거 URL·verified=true를 `data/coordinates.csv`에 넣으면 추정점보다 우선한다.
추정점별 위치 유형·원주소·출처는 `data/coordinates_estimated.csv`와 지도 팝업에 공개한다.
행정경계: Statistics Korea SGIS / mapcn-kr (CC BY 4.0). 지도·동·도로 객체: © OpenStreetMap contributors (ODbL).
비교시설 5개 미만이면 상대효율을 표시하지 않고 사유를 제시한다.

유입량은 일평균 값을 연간 환산한 분모이다. BOD 제거질량은 연평균값의 곱에 의한 근사이며,
전력 간접배출 추정은 2025 승인 2021–2023 평균 소비단 계수 0.4330 tCO₂eq/MWh를 사용한다.
시설 전체 배출·법정 명세서·실증 감축량과 동일하지 않다. 전력의 계통구매·자체생산 구분이 없어 표준화 비교량으로 사용한다.
AI 예측은 달성 가능한 최적 전력량이 아니며 시뮬레이터 절감률의 근거로 쓰지 않는다.

## 제출 전 남은 확인

공식 공모전 제출 양식·참가자 정보는 제공되지 않아 활용 내역서를 전사 가능한 Markdown 초안으로 작성했다.
공식 양식 전사, 연구자 최종 검토, 원본 라이선스 확인과 현장 운영 경계 확인은 별도 필요하다.
희소 비교집단을 가상 데이터로 보완하지 않았다. 지도점은 실측 시설 좌표가 아니라 주소에 근거한 추정임을 표시한다.
'''
    api = data.get('operational_api', {'available': False, 'reason': 'API 원본 수집 전'})
    reports['OPERATIONAL_API_REPORT.md'] = report_hasu(api)
    if api.get('available'):
        reports['DATA_SOURCES.md'] += f'''\n## 추가 확보: 하수 처리 현황 GW (15157553)\n\n[공식 API]({api['source_url']}). XML. 이용허락범위 제한 없음.\n응답 운영일 {api['start_date']}~{api['end_date']}, {api['raw_records']:,}행.\n공식 응답 스키마와 원본 XML은 `data/raw/hasu_api/`에 보존했다.\n조회일과 운영일의 차이를 검증하고 opdate 기준으로 집계했다. 인증키는 `.env.local`에만 저장한다.\n상세 컬럼·결측·사용 범위는 [API 검증 보고서](OPERATIONAL_API_REPORT.md) 참조.\n'''
        reports['DATA_QUALITY_REPORT.md'] += f'''\n## 일별 API 자료의 별도 품질 검증\n\n{api['request_days']}회 일별 조회, 완전 수집 확인 {api['complete_request_days']}회.\n방류수 농도는 원문 meter와 opdate만 사용하고 BMeter·불명확한 전력 단위·PH 단위는 계산에서 제외했다.\n기존 39개 시설의 연간 전력·탄소·전국 비교·모델 값을 이 API로 덮어쓰지 않았다.\n사업소별·항목별 365일 대비 결측률과 중복 격리 내역은 [API 검증 보고서](OPERATIONAL_API_REPORT.md)에 공개한다.\n'''
        reports['ANALYSIS_REPORT.md'] += f'''\n## 일별 방류수 수질 보강 분석\n\n공식 API에서 2025년 {api['operation_days']}개 운영일의 원본 {api['raw_records']:,}행을 확보했다.\n방류 TOC·T-N·T-P·SS의 월별 관측 평균과 유효 일수를 별도로 시각화한다.\n월별 값은 유량 가중이 아닌 일 관측값의 단순 평균이다. 에너지 일별 전력량이 검증되지 않아\n수질의 계절 변화와 전력 절감의 인과관계·월별 에너지 효율은 산출하지 않았다.\n사업소명은 API 표기를 유지하며 연간 통계 시설에 임의 매칭하지 않았다.\n재현 가능한 상세 통계: [운영 API 보고서](OPERATIONAL_API_REPORT.md).\n'''
        reports['README.md'] += '''\n## 인증 API의 재수집과 보강\n\n사용자가 승인한 공공데이터 API 키는 gitignored `.env.local`의 `HASU_SERVICE_KEY`로만 보관한다.\n`.env.example`에는 빈 변수명만 있으며 `VITE_` 접두사를 사용하지 않는다. 웹에서 API를 직접 호출하지 않는다.\n`python scripts/collect_hasu.py --year 2025`로 서버 측에서 일별 XML을 수집한 후\n`python -m analysis.pipeline`을 실행한다. 수집된 원본만 있으면 이후 분석은 인증키 없이 오프라인 재현 가능하다.\n[운영 API 검증 보고서](OPERATIONAL_API_REPORT.md)에 조회일·관측일 차이와 전 컬럼 의미·집계 범위를 기록했다.\n'''
        reports['AI_PROMPT_LOG.md'] += '\n추가 실제 사용자 입력: 대구 하수 처리 현황 API endpoint와 인증키를 제공하고 수집을 승인함. 인증키 값은 활용 내역서에 기재하지 않는다. API 응답 검증·2025년 일별 수집·월별 방류수 집계 코드를 구현했다.\n'
        reports['PUBLIC_DATA_USAGE.md'] += '\n추가 데이터: 대구공공시설관리공단 하수 처리 현황 GW (15157553), 2025년 일별 방류수 농도와 품질 보강. 출처·표본·단위·가공 근거는 OPERATIONAL_API_REPORT.md 참조.\n'
    reports['README.md'] += '''
## 공식 제공 방식과 GitHub 재현

[한국환경공단 공공하수처리시설 현황(3073222)](https://www.data.go.kr/data/3073222/fileData.do)은 CSV 파일데이터다. 전국 시설 원본을 `scripts/acquire.py`로 수집하고 공식 하수도통계 XLSX와 대조해 분석한다.

[대구공공시설관리공단 하수 처리 현황(15157553)](https://www.data.go.kr/data/15157553/openapi.do)은 인증이 필요한 XML 오픈API다. 일별 방류수질 보강에 사용한다. `scripts/collect_hasu.py`는 실패 날짜와 오류 유형을 기록한 뒤 비정상 종료한다. 성공한 XML만 캐시하므로 재실행으로 미완료 요청을 재시도할 수 있다.

처음 실행할 때 `.env.example`을 `.env.local`로 복사하고 개인 `HASU_SERVICE_KEY`를 입력한다. 원본이 없다면 `python scripts/acquire.py`, `python scripts/collect_hasu.py --year 2025`, `python -m analysis.pipeline` 순서로 실행한다. 키는 브라우저 코드·분석 JSON·Git 기록에 넣지 않는다. 이미 생성된 실제 데이터 JSON은 키 없이 정적 웹사이트에서 읽을 수 있다.

원본 XLSX·PDF와 일별 XML은 로컬 `data/raw/`에 보존하며 Git에는 포함하지 않는다. `public/data/analysis.json`과 검증용 CSV·보고서는 실제 수집 결과를 포함한다. 모든 Python 테스트와 분석 재현은 원본을 다시 확보한 후 실행한다. `scripts/acquire.py`가 자동으로 확보하지 못한 자료의 수동 다운로드 위치는 [DATA_SOURCES.md](DATA_SOURCES.md)에 적었다.

[최종 코드·분석 검증](FINAL_AUDIT.md)에 테스트와 남은 확인 범위를 기록했다.
'''
    downloads = ROOT / 'public/downloads'; downloads.mkdir(parents=True, exist_ok=True)
    for name, content in reports.items():
        (ROOT/name).write_text(content,encoding='utf-8')
        (downloads/name).write_text(content,encoding='utf-8')
    for name in ['daegu_2025.csv','national_2025.csv','daegu_predictions.csv','model_oof_predictions.csv','xgboost_shap.json','source_manifest.json','year_verification.json','data_quality.json','hasu_effluent_daily_2025.csv','hasu_effluent_monthly_2025.csv']:
        p=ROOT/'data/processed'/name
        if p.exists(): shutil.copy2(p,downloads/name)
