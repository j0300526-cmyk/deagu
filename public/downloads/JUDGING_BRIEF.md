# 대구 하수처리시설의 숨은 탄소격차 — 심사 요약

**제출 부문:** 공공데이터 분석·시각화

**웹사이트:** https://deagu-phi.vercel.app
**관측 기준:** 2025년. 전년 비교만 2024년을 별도 사용한다.

## 작품이 답하려는 질문

대구 하수처리시설의 전력은 어디에 집중되어 있으며, 수질 정화 성능을 유지하면서 어떤 시설과 공정을 먼저 진단해야 하는가?

## 평가 항목별 확인 위치

| 평가 항목 | 작품의 근거 | 웹에서 볼 곳 |
| --- | --- | --- |
| 주제 적합성 · 25점 | 대구 39개 하수처리시설의 연간 전력 136.71 GWh, 전력 사용에 따른 간접배출 추정 59,196 tCO₂eq. 전력 상위 5개 시설이 90.8%를 사용한다. | [핵심 발견](https://deagu-phi.vercel.app/#overview), [시설 지도](https://deagu-phi.vercel.app/#map) |
| 데이터·AI 활용성 · 30점 | 한국환경공단 2025년 전국 4,556개 시설 자료를 공식 통계와 대조했다. 대구공공시설관리공단 API의 실제 운영일 365일 기록을 별도로 검증했다. XGBoost는 타 지역 4,173개 시설의 교차검증 자료로 학습·선택하고 대구 39개 시설을 독립 평가했다. | [자료와 방법](https://deagu-phi.vercel.app/#quality), [AI 분석](https://deagu-phi.vercel.app/#ai) |
| 독창성·실현가능성 · 25점 | 처리 규모·공법·BOD 부하를 맞춘 비교에서 화북이주단지의 전력 원단위는 유사시설 5개 중앙값의 6.53배였다. 다사 달천은 유입량당 전력 순위 11위, BOD 제거 근사질량당 전력 순위 26위다. 이 차이를 공정별 계측→조건 확인→수질 유지 실증의 순서로 연결했다. | [전국 비교](https://deagu-phi.vercel.app/#benchmark), [실행 제안](https://deagu-phi.vercel.app/#policy) |
| 파급효과 · 20점 | 전력 10% 절감을 **가정**하면 13.67 GWh/년, 공식 계수 환산 5,919.6 tCO₂eq/년의 잠재량이다. 시민 설명용 1페이지 인포그래픽을 제공한다. | [탄소 계산](https://deagu-phi.vercel.app/#carbon), [인포그래픽](https://deagu-phi.vercel.app/downloads/daegu_carbon_lab_research_poster.pdf) |

## 수치를 읽을 때 지켜야 할 범위

- 59,196 tCO₂eq/년은 관측 전력량에 공식 전력배출계수를 곱한 **표준화 간접배출 추정**이다. 시설 전체 온실가스 배출량이 아니다.
- 5,919.6 tCO₂eq/년은 일률 10% 절감 **가정 시나리오**다. 검증된 감축 성과나 현장 달성 목표가 아니다.
- 유사시설 중앙값과 AI 예측값은 가능한 최적 운전값이 아니다. 규모·공법·오염부하 이외의 운영 조건을 현장에서 확인해야 한다.
- BOD 제거율은 유입·방류 **농도** 기반이며, 법정 방류수 기준 충족 판정과 다르다.
- 지도점 39개는 공개 주소를 행정구역·동·도로 대표점에 연결한 **추정 위치**다. 시설 부지 좌표가 아니다.

## 재현 근거

[DATA_SOURCES.md](DATA_SOURCES.md) · [DATA_QUALITY_REPORT.md](DATA_QUALITY_REPORT.md) · [ANALYSIS_REPORT.md](ANALYSIS_REPORT.md) · [MODEL_EVALUATION.md](MODEL_EVALUATION.md) · [AI_PROMPT_LOG.md](AI_PROMPT_LOG.md) · [PUBLIC_DATA_USAGE.md](PUBLIC_DATA_USAGE.md)

분석은 `python -m analysis.pipeline`로 재생성한다. 웹 화면의 수치는 생성된 `public/data/analysis.json`을 사용한다.
