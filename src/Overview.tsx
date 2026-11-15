import { ArrowRight, ArrowUpRight, Database, Droplets, FlaskConical, MapPin } from 'lucide-react';
import type { Analysis, Facility } from './types';
import { fmt, Source } from './components';
import { calculateScenario } from './scenario';

type Props = { data: Analysis; onSelect: (facility: Facility) => void; go: (page: string) => void };

export default function Overview({ data, onSelect, go }: Props) {
  const city = data.summary.daegu;
  const national = data.summary.national;
  const topFive = data.facilities.toSorted((a, b) => (b.electricity_kwh ?? 0) - (a.electricity_kwh ?? 0)).slice(0, 5);
  const topShare = topFive.reduce((sum, facility) => sum + (facility.electricity_kwh ?? 0), 0) / city.electricity_kwh * 100;
  const peerFacility = data.facilities.find(facility => facility.name === '화북이주단지');
  const peer = peerFacility ? data.peers[peerFacility.facility_id] : undefined;
  const rankFacility = data.facilities.find(facility => facility.name === '다사 달천');
  const scenario = calculateScenario(city.electricity_kwh, 10, data.meta.factor.value);
  const maxIntensity = Math.max(city.weighted_kwh_m3, national.weighted_kwh_m3);

  return <>
    <section className="story-lead" aria-labelledby="story-question">
      <div className="story-lead-copy">
        <span className="eyebrow">DAEGU · PUBLIC DATA STORY / 2025</span>
        <h2 id="story-question">어디부터 전력을 살피면<br/><em>대구 전체에 영향이 클까?</em></h2>
        <p>하수를 깨끗하게 처리하면서 전력을 줄일 방법을 찾기 위해, 39개 시설의 사용량·수질·전국 유사시설을 함께 비교했습니다.</p>
        <div className="story-lead-actions">
          <button className="button primary" onClick={() => go('benchmark')}>비교 결과 보기 <ArrowRight size={16}/></button>
          <button className="text-button" onClick={() => go('map')}>시설 위치 보기 <MapPin size={15}/></button>
        </div>
      </div>
      <div className="story-lead-visual">
        <span className="story-overline">첫 번째 발견 · 전력 사용의 집중</span>
        <strong>{fmt(topShare, 1)}<small>%</small></strong>
        <p>전력 사용 상위 5개 시설이<br/>대구 39개 시설의 총전력에서 차지하는 비중</p>
        <div className="story-share-bar" role="img" aria-label={'2025년 대구 전력 사용 상위 5개 시설 ' + fmt(topShare, 1) + '%, 나머지 ' + fmt(100 - topShare, 1) + '%'}>
          <span style={{ width: String(topShare) + '%' }} />
        </div>
        <div className="story-share-labels"><span>상위 5개</span><span>나머지 {city.n - topFive.length}개</span></div>
        <p className="story-topnames">{topFive.map(facility => facility.name).join(' · ')}</p>
        <p className="story-visual-note">따라서 총량 관리의 첫 계측 대상은 대형 시설입니다. <b>전력 사용량이 크다고 비효율이라는 뜻은 아닙니다.</b></p>
        <small>{data.meta.year}년 · 한국환경공단 · 연간 총전력 kWh 합계</small>
      </div>
    </section>

    <div className="story-facts" aria-label="대구 하수처리시설 핵심 관측값">
      <article><Database size={19}/><span>분석한 대구 시설</span><strong>{city.n}<small>개소</small></strong><p>전국 {fmt(national.n, 0)}개 중 대구 시설</p></article>
      <article><FlaskConical size={19}/><span>연간 전력 사용</span><strong>{fmt(city.electricity_kwh / 1e6, 1)}<small>GWh</small></strong><p>시설별 관측 전력량 합계</p></article>
      <article><ArrowUpRight size={19}/><span>전력 간접배출 추정</span><strong>{fmt(city.indirect_tco2e_est / 1000, 1)}<small>천 tCO₂eq</small></strong><p>공식 계수 환산 · 시설 전체 배출량 아님</p></article>
      <article><Droplets size={19}/><span>수질을 함께 확인</span><strong>{fmt(city.median_bod_removal_pct, 1)}<small>%</small></strong><p>BOD 농도 제거율 중앙값 · 법정 판정 아님</p></article>
    </div>
    <p className="story-facts-source">{data.meta.year}년 · 한국환경공단 공공하수처리시설 현황 · 전력 간접배출에만 GIR 공식 전력배출계수 적용</p>

    <div className="story-section-heading">
      <span className="eyebrow">THREE THINGS THE DATA CHANGES</span>
      <h2>숫자 하나로 시설을 줄 세우지 않는 이유</h2>
      <p>처리 규모, 비슷한 시설, 제거한 오염량을 함께 보면 판단이 달라집니다.</p>
    </div>
    <div className="story-evidence-grid">
      <article className="story-evidence story-evidence-wide">
        <span className="story-card-number">01 / 도시 전체와 개별 시설</span>
        <h3>도시 전체 수치가 낮아도<br/>모든 시설이 효율적인 것은 아닙니다.</h3>
        <p className="story-chart-intro">하수 1m³를 처리하는 데 든 전력</p>
        <div className="story-compare-bars" role="img" aria-label={'2025년 유입량 가중 전력 원단위 대구 ' + fmt(city.weighted_kwh_m3, 3) + ', 전국 ' + fmt(national.weighted_kwh_m3, 3) + ' kWh/m³'}>
          {[{ label: '대구', value: city.weighted_kwh_m3 }, { label: '전국', value: national.weighted_kwh_m3 }].map(row =>
            <div key={row.label}><span>{row.label}</span><i><b style={{ width: String(row.value / maxIntensity * 100) + '%' }} /></i><strong>{fmt(row.value, 3)}</strong></div>)}
        </div>
        <p className="story-card-meaning">대구 전체는 <b>{fmt(city.weighted_kwh_m3, 3)} kWh/m³</b>입니다. 시설 하나를 평가할 때는 규모·공법·오염부하가 비슷한 곳과 비교해야 합니다.</p>
        <small>{data.meta.year}년 · 한국환경공단 · 전력 합계 ÷ 연간 환산 유입량 합계 · 전국과 대구의 시설 구성 차이 포함</small>
      </article>

      {peer?.available && peerFacility && <article className="story-evidence">
        <span className="story-card-number">02 / 비슷한 시설과 비교</span>
        <h3>추가 진단이 필요한 곳은<br/>다르게 드러납니다.</h3>
        <div className="story-peer-visual"><strong>{fmt(peer.ratio, 2)}<small>배</small></strong><span>{peerFacility.name}</span></div>
        <div className="story-peer-baseline"><span>이 시설 {fmt(peerFacility.kwh_m3, 3)} kWh/m³</span><span>유사시설 중앙값 {fmt(peer.median_kwh_m3, 3)} kWh/m³</span></div>
        <p className="story-card-meaning">전력 원단위가 타 지역 유사시설 {peer.count}개의 중앙값보다 높습니다. <b>절감 가능량이 아니라 현장 확인 순서의 단서</b>입니다.</p>
        <button className="story-inline-link" onClick={() => onSelect(peerFacility)}>비교집단 확인 <ArrowUpRight size={15}/></button>
        <small>{data.meta.year}년 · 한국환경공단 · kWh/m³ · 공법·규모·BOD 부하를 맞춘 비교</small>
      </article>}

      {rankFacility && <article className="story-evidence">
        <span className="story-card-number">03 / 무엇을 처리했는가</span>
        <h3>물의 양만 보면<br/>순위가 달라집니다.</h3>
        <div className="story-rank-visual"><div><span>하수 1m³당 전력</span><strong>{fmt(rankFacility.rank_volume, 0)}위</strong></div><ArrowRight size={27}/><div><span>BOD 1kg 제거당 전력</span><strong>{fmt(rankFacility.rank_bod, 0)}위</strong></div></div>
        <p className="story-card-meaning">{rankFacility.name}은 두 기준에서 다른 위치에 있습니다. <b>유량과 오염물질 제거량을 함께 공개</b>해야 하는 이유입니다.</p>
        <button className="story-inline-link" onClick={() => onSelect(rankFacility)}>시설 수치 확인 <ArrowUpRight size={15}/></button>
        <small>{data.meta.year}년 · 대구 {city.n}개 시설 내 순위 · BOD 제거 질량은 연평균 농도·유량 기반 근사</small>
      </article>}
    </div>

    <section className="story-action" aria-labelledby="story-action-title">
      <div><span className="eyebrow">WHAT DAEGU CAN TEST NEXT</span><h2 id="story-action-title">계측하고, 원인을 확인하고,<br/>수질을 지키며 실증합니다.</h2><p>전력 절감은 공정별 계측과 방류수질 검증이 함께 이뤄질 때 정책 성과로 평가할 수 있습니다.</p><button className="button secondary" onClick={() => go('policy')}>3단계 실행 제안 <ArrowRight size={16}/></button></div>
      <div className="story-scenario"><span>만약 대구 전력의 10%를 줄인다면</span><strong>{fmt(scenario.carbon, 0)}<small>tCO₂eq/년</small></strong><p>{fmt(scenario.saving / 1e6, 2)} GWh/년의 전력 절감에 공식 계수를 곱한 값입니다.</p><b>가정 시나리오 · 실증된 감축량 아님</b><button className="story-inline-link" onClick={() => go('carbon')}>절감률 바꿔 보기 <ArrowUpRight size={15}/></button></div>
    </section>

    <section className="story-method" aria-labelledby="story-method-title"><div><span className="eyebrow">PUBLIC DATA + AI</span><h2 id="story-method-title">이 결론은 어떻게 만들었나</h2><p>공공데이터에서 관측값을 확보하고, AI는 전력 차이에 관련된 조건을 탐색하는 데 사용했습니다.</p></div><ol><li><b>01</b><strong>공식 자료 수집</strong><span>전국 {fmt(national.n, 0)}개 · 대구 {city.n}개 시설</span></li><li><b>02</b><strong>조건을 맞춰 비교</strong><span>규모·공법·BOD 부하와 수질을 함께 확인</span></li><li><b>03</b><strong>AI로 패턴 점검</strong><span>타 지역 {fmt(data.model.train_n, 0)}개 학습 · 대구 {data.model.daegu_n}개 독립 평가</span></li></ol><button className="story-inline-link" onClick={() => go('ai')}>AI 분석 근거 보기 <ArrowUpRight size={15}/></button></section>
    <Source data={data}/>
  </>;
}
