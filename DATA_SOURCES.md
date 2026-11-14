# 공공데이터 출처 및 활용 내역

확인일: 2026-11-13 (Asia/Seoul). 주 분석 관측연도: 2025년. 전년 비교: 2024년.

| 출처 | 자료·기준연도 | 활용 | 이용 조건 |
| --- | --- | --- | --- |
| [한국환경공단 공공하수처리시설 현황](https://www.data.go.kr/data/3073222/fileData.do) | CSV 파일명 20251231 / 4,556행·60열 | 전국·대구 수질, 전력, 공법·부하 비교 | 포털: 이용허락범위 제한 없음; 출처 명시 |
| [환경부 하수도통계 공식 자료목록](https://www.mcee.go.kr/home/web/public_info/read.do?publicInfoId=640&menuId=10123) | 2025 통계, 2026-07-31 게시; 2024 통계, 2025-11-10 게시 | CSV 관측연도·단위 검증; 2024 비교; 2025 슬러지·재이용 총량 | 원본 저작권·이용조건 확인 필요. 사실 수치·가공 결과 출처 명시 |
| [한국환경공단 하수도정보](https://www.data.go.kr/data/15137402/fileData.do) | 제공된 9개 CSV, 각 행의 년도 기준 | 지역·연도 통계 별도 프로파일. 관측연도·집계수준이 달라 시설 모델에 결합하지 않음 | 포털: 이용허락범위 제한 없음 |
| [GIR 2025 승인 계수](https://www.gir.go.kr/home/board/read.do?boardMasterId=2&boardId=86&menuId=36) | 2025-12-18 공표 / 2021–2023 평균 | 소비단 0.4330 tCO₂eq/MWh. 2023 단년도 0.4173과 구분 | 공식 공표 수치 인용; PDF 별도 개방 라이선스 미확인 |
| [GIR 2024 승인 계수](https://www.gir.go.kr/home/board/read.do?boardMasterId=2&boardId=82&menuId=36) | 2025-03-31 공표 / 2020–2022 평균 | 2024 CSV의 참고 환산량 0.4541 tCO₂eq/MWh. 연도별 탄소 추이는 제시하지 않음 | 공식 공표 수치 인용; PDF 별도 개방 라이선스 미확인 |
| [대구 하수관거 및 관로 현황](https://www.data.go.kr/data/3045606/fileData.do) | 20260101 파일 / 89행 | 관로 보강자료 보존·프로파일; 시설 좌표로 전환하지 않음 | 포털: 이용허락범위 제한 없음 |
| [OpenStreetMap](https://www.openstreetmap.org/copyright) | 현재 지도 배경 | 위치 참고용 배경. 통계 관측자료와 별도 | © OpenStreetMap contributors / ODbL |

## 원본 확보 및 연도 확정

기존 제공 파일은 원래 위치에 두고 `data/raw/`에 그대로 복사했다. 포털 다운로드 엔드포인트에서
전국 CSV를 다시 다운로드한 파일은 `facilities_portal_download.csv`이다. 기존 CSV와 SHA-256이 일치했다.
메타데이터의 시간범위(2015–2024)와 파일명(20251231)이 서로 일관되지 않아, 파일명만으로 관측연도를 정하지 않았다.
공식 2025 XLSX의 개별 시설행과 CSV의 13개 필드(시도·시설명·주소·용량·유량·BOD·TOC·T-N·T-P·공법·전력)를
4,556행 전수 대조해 모두 일치함을 확인했다. 비교 코드: `analysis/core.py: verify_2025`.
근거: `data/processed/year_verification.json`, 원본 헤더·본문: `statistics_2025_catalog.xlsx`.

## 다시 다운로드하는 방법

`python scripts/acquire.py`는 로그인 없이 공개된 파일만 다운로드한다. 현재 확보 파일로 분석은 오프라인 실행 가능하다.
접근이 막히거나 CAPTCHA가 나오면 우회하지 말고 다음을 수행한다.

1. 공공데이터포털 3073222에서 다운로드 → `data/raw/facilities_portal_download.csv`로 보관.
2. 위 환경부 공식 자료목록에서 “2025 하수도통계(최종).xlsx”, “2024 하수도통계(최종)★.xlsx” 다운로드 → 각각 `statistics_2025_catalog.xlsx`, `statistics_2024_catalog.xlsx`.
3. GIR 게시글 86의 PDF 다운로드 → `data/raw/gir_2025.pdf`. 게시글 82의 PDF는 `gir_2024.pdf`.
4. 15137402에서 연결되는 국가하수도정보시스템의 통계별 CSV는 기존 `data/raw/한국환경공단_하수도정보/`에 보존. 재수집 시 기준연도·단위를 함께 저장.
5. 좌표가 필요하면 공식 시설 좌표와 근거 URL을 확인해 `data/coordinates.csv`에 입력. 지오코딩 추정값으로 대체하지 않는다.

## 표준 컬럼과 단위

시설용량·유입·방류량은 공식 XLSX의 `6. 공공하수처리시설(전체)` 표 머리글에 m³/일로 표시된다.
유입량은 연간 적산량이 아닌 일평균 규모 지표로 사용하고 2025년 365일, 2024년 366일을 곱해 연간 환산한다.
연간 유량과 농도를 곱한 BOD 부하는 연평균의 곱으로 근사한 값이며 적산 실측 오염부하와 다르다.
재이용 표의 연간 하수처리량은 방류량과 대응하는 천톤/년 지표로, 유입량 분모와 혼용하지 않는다.

| 표준 컬럼 | 원본 의미 | 단위 |
| --- | --- | --- |
| region | 시도 | 문자열 |
| district | 구군 | 문자열 |
| name | 시설명 | 문자열 |
| address | 소재지 | 문자열 |
| capacity_m3_day | 시설용량 | m³/일 |
| inflow_m3_day | 유입하수량 | m³/일 |
| outflow_m3_day | 방류량 | m³/일 |
| bod_in | 유입 BOD | mg/L |
| bod_out | 방류 BOD | mg/L |
| toc_in | 유입 TOC | mg/L |
| toc_out | 방류 TOC | mg/L |
| tn_in | 유입 T-N | mg/L |
| tn_out | 방류 T-N | mg/L |
| tp_in | 유입 T-P | mg/L |
| tp_out | 방류 T-P | mg/L |
| method | 처리방법 | 문자열 |
| linked_feces | 연계처리량 분뇨 | m³/일 |
| linked_livestock | 연계처리량 축산 | m³/일 |
| linked_leachate | 연계처리량 침출수 | m³/일 |
| linked_other | 연계처리량 기타 | m³/일 |
| started | 가동개시일 | 날짜 |
| self_sufficiency_pct | 에너지자립율 | % |
| energy_production_toe | 에너지 자체생산량 | TOE/년 |
| electricity_kwh | 연간 총전력사용량 | kWh/년 |
| reported_co2_kg_m3 | 원자료 하수처리량당 CO₂ 배출량 | kgCO₂/m³ |

원본 60개 컬럼 전체 결측률·사용 여부·단위는 DATA_QUALITY_REPORT.md 및 `data/processed/data_quality.json`에 기록했다.
전 파일 해시는 `data/processed/source_manifest.json`에 있다. SHA는 무결성 근거이며 데이터 내용의 정확성을 보증하지 않는다.

## 추가 확보: 하수 처리 현황 GW (15157553)

[공식 API](https://www.data.go.kr/data/15157553/openapi.do). XML. 이용허락범위 제한 없음.
응답 운영일 2025-01-01~2025-12-31, 258,050행.
공식 응답 스키마와 원본 XML은 `data/raw/hasu_api/`에 보존했다.
조회일과 운영일의 차이를 검증하고 opdate 기준으로 집계했다. 인증키는 `.env.local`에만 저장한다.
상세 컬럼·결측·사용 범위는 [API 검증 보고서](OPERATIONAL_API_REPORT.md) 참조.
