# DAEGU CARBON LAB

### 대구 하수처리시설의 숨은 탄소격차

**대구 하수시설의 전기, 어디부터 살펴볼까?**

2026 대구광역시 기후·환경·탄소중립 공공데이터 AI 활용대회 **부문 2 · 공공데이터 분석·시각화** 출품작

**[웹사이트 열기](https://deagu-phi.vercel.app/)** · [1페이지 인포그래픽](public/downloads/daegu_carbon_lab_research_poster.pdf) · [분석보고서](ANALYSIS_REPORT.md)

> **한 문장 결론:** 대구 하수시설의 전력은 일부 큰 시설에 집중된다. 그 시설들의 공정별 사용처를 먼저 측정하고, 효율은 비슷한 시설과 비교한 뒤, 수질을 지키는 절감 실험으로 검증해야 한다.

## 숫자 세 개로 읽기

| 2025년 분석 결과 | 의미 | 주의할 점 |
| --- | --- | --- |
| **90.8%** | 대구 39개 시설 중 전력 사용 상위 5곳의 비중 | 많이 쓴다고 비효율이라는 뜻은 아니다. |
| **6.53배** | 화북이주단지의 하수 1m³당 전력이 유사한 타 지역 시설 5곳의 중앙값 대비 높은 정도 | 현장 진단 단서다. 절감 가능률이 아니다. |
| **5,920 tCO₂eq/년** | 대구 전체 전력을 10% 줄인다고 **가정**했을 때의 간접배출 감소량 | 실증 성과나 시설 전체 배출량이 아니다. |

첫째는 **전력의 집중**, 둘째는 **비교 결과**, 셋째는 **가정 시나리오**다.

```mermaid
flowchart LR
    A["전력은 어디에 모이나?<br/>상위 5곳 · 90.8%"] --> B["왜 차이가 나나?<br/>비슷한 시설끼리 비교"]
    B --> C["실제로 줄일 수 있나?<br/>공정별 계측·방류수질 실증"]
    C --> D["탄소 영향은?<br/>검증된 절감량에 공식 계수 적용"]
```

## 웹사이트 읽는 순서

처음 방문했다면 **① → ③ → ⑥**만 읽어도 연구의 질문·근거·제안을 이해할 수 있다.

| 화면 | 여기서 확인할 것 |
| --- | --- |
| [① 질문과 결론](https://deagu-phi.vercel.app/#overview) | 무엇을 발견했고 대구에서 무엇부터 해야 하는가 |
| [② 시설 찾기](https://deagu-phi.vercel.app/#map) | 시설 위치와 전력·수질. 지도점은 주소 기반 **추정 위치** |
| [③ 전국과 비교](https://deagu-phi.vercel.app/#benchmark) | 같은 규모·공법·오염부하의 시설과 비교하면 무엇이 다른가 |
| [④ AI로 살펴보기](https://deagu-phi.vercel.app/#ai) | 예측에 관련된 변수, 모델 오차와 SHAP 설명 |
| [⑤ 탄소 계산](https://deagu-phi.vercel.app/#carbon) | 절감률에 따른 **가정상** 전력 간접배출 감소량 |
| [⑥ 실행 제안](https://deagu-phi.vercel.app/#policy) | 계측 → 원인 확인 → 수질 유지 실증의 현장 적용 순서 |

## 데이터는 어디서 왔나

- **시설별 전력·수질·공법:** [한국환경공단 공공하수처리시설 현황](https://www.data.go.kr/data/3073222/fileData.do). 2025년 전국 4,556곳 중 대구 39곳.
- **연도·단위 검증:** [환경부 하수도통계](https://www.mcee.go.kr/home/web/public_info/read.do?publicInfoId=640&menuId=10123), 2024·2025년.
- **대구 일별 방류수질:** [대구공공시설관리공단 하수 처리 현황 API](https://www.data.go.kr/data/15157553/openapi.do). 연간 전력 자료와 시설을 임의로 매칭하지 않았다.
- **전력 간접배출:** [온실가스종합정보센터 공식 계수](https://www.gir.go.kr/home/board/read.do?boardMasterId=2&boardId=86&menuId=36), 0.4330 tCO₂eq/MWh.

원본별 기준연도·라이선스·다운로드 방법과 추가 자료는 [DATA_SOURCES.md](DATA_SOURCES.md)에 있다. 웹사이트는 분석 코드가 만든 [analysis.json](public/data/analysis.json)을 읽으며 가상 관측값을 사용하지 않는다.

## 바로 실행하기

실제 데이터 JSON이 저장돼 있어 웹사이트만 실행할 때는 API 키나 Python이 필요하지 않다.

```powershell
npm ci
npm run dev
```

터미널에 표시된 주소(기본 http://127.0.0.1:5173)를 연다. Vercel은 Vite 빌드 `npm run build`, 출력 폴더 `dist`를 사용한다.

### 원본에서 분석 다시 만들기

Python 3.14, Node 24에서 검증했다. 공식 API를 다시 수집할 때만 `.env.example`을 `.env.local`로 복사하고 본인의 `HASU_SERVICE_KEY`를 입력한다. 키는 브라우저·Git에 넣지 않는다.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/acquire.py
python scripts/collect_hasu.py --year 2025
python -m analysis.pipeline
```

일부 원본은 수동 다운로드가 필요할 수 있다. 파일명과 경로는 [DATA_SOURCES.md](DATA_SOURCES.md)에 있다. 수집 실패 시 원본을 만들어 넣지 않는다.

### 검증

```powershell
python -m pytest -q
npm run test:render
npm run build
```

## 결과를 해석하는 경계

- 유입량은 공식 자료의 **m³/일** 값을 연간 환산했다. BOD 제거질량은 연평균 농도와 유량의 곱에 의한 **근사**다.
- 전력 간접배출은 연간 전력 × 공식 전력배출계수다. 시설의 직접배출과 전체 온실가스 배출을 포함하지 않는다.
- AI 예측값은 관측값도, 달성 가능한 최적 전력량도 아니다. 상관관계나 SHAP 중요도를 원인으로 단정하지 않는다.
- 지도점은 주소에 근거한 행정구역·동·도로의 대표점이며 **시설 부지 좌표가 아니다.** 지도 자료: Statistics Korea SGIS / mapcn-kr(CC BY 4.0), © OpenStreetMap contributors(ODbL).
- 비교집단이 5곳 미만이면 상대 효율을 표시하지 않는다. 탄소 시뮬레이터는 실증 효과가 아닌 가정이다.

## 상세 자료와 코드

| 자료 | 내용 |
| --- | --- |
| [ANALYSIS_REPORT.md](ANALYSIS_REPORT.md) | 계산 결과, 비교 기준, 정책 시사점 |
| [DATA_QUALITY_REPORT.md](DATA_QUALITY_REPORT.md) | 결측·단위·연도와 품질 검증 |
| [MODEL_EVALUATION.md](MODEL_EVALUATION.md) | 기준모델·Random Forest·XGBoost 평가와 SHAP |
| [OPERATIONAL_API_REPORT.md](OPERATIONAL_API_REPORT.md) | 대구 일별 방류수질 API의 수집·검증 범위 |
| [PUBLIC_DATA_USAGE.md](PUBLIC_DATA_USAGE.md) · [AI_PROMPT_LOG.md](AI_PROMPT_LOG.md) | 공모전 활용 내역 초안 |
| [JUDGING_BRIEF.md](JUDGING_BRIEF.md) · [FINAL_AUDIT.md](FINAL_AUDIT.md) | 심사 관점 요약과 최종 검증 |

분석 코드는 `analysis/`, 수집 코드는 `scripts/`, React 화면은 `src/`, 웹용 결과는 `public/data/`에 있다. `data/raw/`의 원본은 Git에 포함하지 않는다. 분석 파이프라인은 보고서를 다시 생성하며, 이 README는 읽기 쉬운 프로젝트 안내서로 별도 유지된다.
