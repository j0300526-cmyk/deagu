# 실행·검증 기록

검증일: 2026-11-13 (Asia/Seoul).

사용자 흐름: 공식 원본 → Python 전처리·통계·시설 그룹 모델 평가 → 정적 JSON/CSV → HTTP 제공 → React 분석 화면 → 시설 비교·가정 시나리오·근거 보고서.

| 경계 | 결과 | 근거 |
| --- | --- | --- |
| 공식 원본 → 관측연도 | 통과 | 2025 XLSX와 CSV 4,556행 × 13개 필드 전수 일치, 기존 CSV와 재다운로드 파일 SHA-256 일치 |
| 원본 → 파생 지표 | 통과 | 일/연 단위, 윤년, BOD 유입·방류 질량수지, 결측 전력 처리, 가중 평균 표본 일치 테스트 |
| 시설 비교·AI | 통과 | 비교시설 공법·용량·유입·부하 범위와 타 지역 조건, GroupKFold 그룹 중복 방지, 대구 독립 평가, 공개 예측에서 평가점수 재계산 |
| JSON → React 콘텐츠 | 통과 | 실제 결과 JSON을 이용한 6개 콘텐츠 화면 서버 렌더링 검사. NaN·undefined 없음. `npm run test:render` |
| 개발 HTTP | 통과 | `/`, `/data/analysis.json`, `/downloads/daegu_2025.csv`, `/downloads/ANALYSIS_REPORT.md` 모두 HTTP 200 |
| 배포 산출물 HTTP | 통과 | production preview의 index·JSON·CSV·보고서·참조 JS/CSS 모두 HTTP 200. 전달된 JSON과 생성 JSON의 SHA-256 일치 |
| 정적 배포 빌드 | 통과 | TypeScript 검사와 Vite production build. `dist/` 생성 |
| 브라우저 시각·클릭·모바일 | 미완료 | 브라우저 접근 호스트 unavailable. Windows 대체 접근도 사용자 입력 감지로 중단. 실제 브라우저 검증 통과로 주장하지 않음 |
| 지도 시설 마커 | 의도적으로 비활성 | 검증 좌표 0개. 빈 GeoJSON. OpenStreetMap 배경과 실제 시설 목록 제공 |
| 실제 Vercel 배포 | 미수행 | 배포 가능한 Vite 구조와 vercel.json만 작성 |

자동 분석 검증: `python -m pytest -q` — 15 passed. 외부 설치 패키지 anyio의 pytest deprecation 경고 1개가 있었으며 프로젝트 테스트 실패는 없었다.

Windows OneDrive 경로에서 기존 출력 폴더를 정리하는 빌드가 native exit `-1073740791`로 종료되는 현상을 관찰했다.
별도 출력 폴더 빌드 및 기존 폴더 정리를 생략하는 설정에서 성공했다. `vite.config.ts`에 `emptyOutDir: false`와
JavaScript 기반 terser 압축을 설정했다. 재빌드 시 이전 해시의 정적 자산이 남을 수 있으나 index.html은 최신 자산을 참조한다.
Vercel의 새 작업 디렉터리에서는 이 잔여 파일이 없다.

브라우저 후속 점검 항목: 6개 메뉴 전환, 시설 상세 열기·닫기, 규모·공법·검색 필터, 모델 전환,
절감률 0/10/30%와 시설별 시나리오, CSV·Markdown 다운로드, 좁은 화면 메뉴·표 스크롤, 지도 타일 네트워크.

## 공식 운영 API 추가 연동 검증

- 사용자 제공 인증키로 공식 `/Hasu/svHasu` 호출 성공. 키는 gitignored `.env.local`에 보관.
- 2025년 관측 365일, 운영 원본 258,050행 확보. 365회 조회의 페이지·전체 건수 일치.
- 전 응답의 관측일이 조회일보다 1일 전임을 확인하고 opdate로 집계.
- 6개 사업소의 방류 TOC·T-N·T-P·SS 8,634행 중 유효 수치 8,579개. 결측 보간 없음.
- 2025년 월별 방류수 차트·관측률·CSV·OPERATIONAL_API_REPORT.md 추가.
- 불명확한 북부 총인 공정의 `kw/일` 전력값과 BMeter는 계산 제외. 기존 연간 전력·모델 관측 범위 유지.
- 추가 검증 포함 `python -m pytest -q`: 21 passed. 실제 API 결과가 포함된 6개 콘텐츠 화면 렌더링 통과.
- TypeScript·Vite 빌드 통과. 인증키 문자열이 소스·원본·가공 결과·웹 산출물에 없는지 자동 검사 통과.
- 브라우저 시각·클릭 검증의 제한은 위 기록과 동일하다.
