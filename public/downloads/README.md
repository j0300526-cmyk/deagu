# DAEGU CARBON LAB

## 대구 하수처리시설의 숨은 탄소격차

2026 대구광역시 기후·환경·탄소중립 공공데이터 AI 활용대회 부문 2 출품용 분석 프로젝트.
전국 4,556개·대구 39개 시설의 실제 2025년 공공데이터를 사용한다.
React + TypeScript + Vite + Tailwind + Recharts + Leaflet, Python/Pandas/NumPy/Scikit-learn/GeoPandas/XGBoost/SHAP.

## 실행

Python 3.14, Node 24에서 검증했다. 패키지 가용성이 다른 환경은 requirements 설치 결과를 확인한다.
API 수집 전에 `.env.example`을 `.env.local`로 복사하고 개인 `HASU_SERVICE_KEY`를 입력한다.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
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
실제 배포는 수행하지 않았다. SPA 내부 화면은 해시 경로를 사용해 새로고침을 지원한다.

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
지도는 검증된 시설 좌표가 없어 시설 마커를 표시하지 않는다. 공식 좌표·근거 URL·verified=true를
`data/coordinates.csv`에 입력하고 재분석하면 Leaflet에 반영된다. OpenStreetMap은 지도 배경으로만 사용한다.
비교시설 5개 미만이면 상대효율을 표시하지 않고 사유를 제시한다.

유입량은 일평균 값을 연간 환산한 분모이다. BOD 제거질량은 연평균값의 곱에 의한 근사이며,
전력 간접배출 추정은 2025 승인 2021–2023 평균 소비단 계수 0.4330 tCO₂eq/MWh를 사용한다.
시설 전체 배출·법정 명세서·실증 감축량과 동일하지 않다. 전력의 계통구매·자체생산 구분이 없어 표준화 비교량으로 사용한다.
AI 예측은 달성 가능한 최적 전력량이 아니며 시뮬레이터 절감률의 근거로 쓰지 않는다.

## 제출 전 남은 확인

공식 공모전 제출 양식·참가자 정보는 제공되지 않아 활용 내역서를 전사 가능한 Markdown 초안으로 작성했다.
공식 양식 전사, 연구자 최종 검토, 원본 라이선스 확인과 현장 운영 경계 확인은 별도 필요하다.
자료가 없는 지도·희소 비교집단을 가상 데이터로 보완하지 않았다.

## 인증 API의 재수집과 보강

사용자가 승인한 공공데이터 API 키는 gitignored `.env.local`의 `HASU_SERVICE_KEY`로만 보관한다.
`.env.example`에는 빈 변수명만 있으며 `VITE_` 접두사를 사용하지 않는다. 웹에서 API를 직접 호출하지 않는다.
`python scripts/collect_hasu.py --year 2025`로 서버 측에서 일별 XML을 수집한 후
`python -m analysis.pipeline`을 실행한다. 수집된 원본만 있으면 이후 분석은 인증키 없이 오프라인 재현 가능하다.
[운영 API 검증 보고서](OPERATIONAL_API_REPORT.md)에 조회일·관측일 차이와 전 컬럼 의미·집계 범위를 기록했다.

## 공식 제공 방식과 GitHub 재현

[한국환경공단 공공하수처리시설 현황(3073222)](https://www.data.go.kr/data/3073222/fileData.do)은 CSV 파일데이터다. 전국 시설 원본을 `scripts/acquire.py`로 수집하고 공식 하수도통계 XLSX와 대조해 분석한다.

[대구공공시설관리공단 하수 처리 현황(15157553)](https://www.data.go.kr/data/15157553/openapi.do)은 인증이 필요한 XML 오픈API다. 일별 방류수질 보강에 사용한다. `scripts/collect_hasu.py`는 실패 날짜와 오류 유형을 기록한 뒤 비정상 종료한다. 성공한 XML만 캐시하므로 재실행으로 미완료 요청을 재시도할 수 있다.

처음 실행할 때 `.env.example`을 `.env.local`로 복사하고 개인 `HASU_SERVICE_KEY`를 입력한다. 원본이 없다면 `python scripts/acquire.py`, `python scripts/collect_hasu.py --year 2025`, `python -m analysis.pipeline` 순서로 실행한다. 키는 브라우저 코드·분석 JSON·Git 기록에 넣지 않는다. 이미 생성된 실제 데이터 JSON은 키 없이 정적 웹사이트에서 읽을 수 있다.

원본 XLSX·PDF와 일별 XML은 로컬 `data/raw/`에 보존하며 Git에는 포함하지 않는다. `public/data/analysis.json`과 검증용 CSV·보고서는 실제 수집 결과를 포함한다. 모든 Python 테스트와 분석 재현은 원본을 다시 확보한 후 실행한다. `scripts/acquire.py`가 자동으로 확보하지 못한 자료의 수동 다운로드 위치는 [DATA_SOURCES.md](DATA_SOURCES.md)에 적었다.

[최종 코드·분석 검증](FINAL_AUDIT.md)에 테스트와 남은 확인 범위를 기록했다.
