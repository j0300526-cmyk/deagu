import { ArrowRight, ArrowUpRight } from 'lucide-react';
import type { Analysis, Facility } from './types';
import { fmt, Source } from './components';
import { calculateScenario } from './scenario';

type Props = { data: Analysis; onSelect: (facility: Facility) => void; go: (page: string) => void };

export default function Overview({ data, onSelect, go }: Props) {
  const city = data.summary.daegu;
  const topFive = data.facilities.toSorted((a, b) => (b.electricity_kwh ?? 0) - (a.electricity_kwh ?? 0)).slice(0, 5);
  const share = topFive.reduce((sum, facility) => sum + (facility.electricity_kwh ?? 0), 0) / city.electricity_kwh * 100;
  const peerFacility = data.facilities.find(facility => facility.name === '화북이주단지');
  const peer = peerFacility ? data.peers[peerFacility.facility_id] : undefined;
  const scenario = calculateScenario(city.electricity_kwh, 10, data.meta.factor.value);
  const comparisonWidth = peer?.ratio ? Math.min(100, 100 / peer.ratio) : 0;

  return <>
    <section className="simple-hero" aria-labelledby="simple-hero-title">
      <div className="simple-hero-copy">
        <span className="eyebrow">분석 결과 ① · 전력 사용 집중</span>
        <h2 id="simple-hero-title">먼저, 전력이 모인<br/><em>5곳의 사용처를 측정합니다.</em></h2>
        <p>대구 시설 {city.n}곳 중 전력 사용이 큰 5곳에서 전체 전력의 {fmt(share, 1)}%를 씁니다. 이곳의 송풍·펌프 등 공정별 전력부터 알아야 절감 대상을 정할 수 있습니다.</p>
        <button className="button primary" onClick={() => go('map')}>시설 지도에서 찾기 <ArrowRight size={16}/></button>
      </div>
      <div className="simple-hero-number">
        <span className="eyebrow">① 전력은 어디에 모이나</span>
        <strong>{fmt(share, 1)}<small>%</small></strong>
        <p>대구 상위 5개 시설의 연간 전력 비중</p>
        <div className="simple-share" role="img" aria-label={'상위 5개 시설이 전체 전력의 ' + fmt(share, 1) + '%를 사용'}><span style={{ width: String(share) + '%' }}/></div>
        <div className="simple-share-label"><span>상위 5곳</span><span>나머지 {city.n - topFive.length}곳</span></div>
        <small>{topFive.map(facility => facility.name).join(' · ')}</small>
      </div>
    </section>
    <p className="simple-boundary">{data.meta.year}년 · 한국환경공단 · 연간 총전력 kWh 기준. 전력을 많이 쓴다는 사실만으로 비효율적인 시설이라는 뜻은 아닙니다.</p>

    <section className="simple-message" aria-label="이 연구의 핵심 제안">
      <span>이 연구의 결론</span>
      <p><b>많이 쓰는 곳은 공정별로 측정하고,</b> 효율은 비슷한 시설과 비교한 뒤, 수질을 지키는 절감 실험으로 검증해야 합니다.</p>
    </section>

    <section className="simple-discoveries" aria-labelledby="simple-discoveries-title">
      <div className="simple-section-title"><span className="eyebrow">다음 질문</span><h2 id="simple-discoveries-title">그다음, 두 가지를 확인합니다</h2></div>
      <div className="simple-cards simple-cards-two">
        {peer?.available && peerFacility && <article>
          <span className="simple-card-step">② 비슷한 시설과 비교하기</span>
          <h3>전력 차이가 큰 곳은 왜 그럴까?</h3>
          <strong>{fmt(peer.ratio, 2)}<small>배</small></strong>
          <div className="simple-compare" role="img" aria-label={peerFacility.name + '의 단위 처리량당 전력이 유사시설 중앙값의 ' + fmt(peer.ratio, 2) + '배'}>
            <div><span>유사시설 중앙값</span><i style={{ width: String(comparisonWidth) + '%' }}/><b>1배</b></div>
            <div><span>{peerFacility.name}</span><i style={{ width: '100%' }}/><b>{fmt(peer.ratio, 2)}배</b></div>
          </div>
          <p>{peerFacility.name}은 규모·공법·BOD 부하가 비슷한 타 지역 {peer.count}곳의 중앙값보다 하수 1m³당 전력 사용이 높습니다. 계측 범위와 운영조건을 현장에서 확인할 대상입니다.</p>
          <button onClick={() => onSelect(peerFacility)}>시설 수치 확인 <ArrowUpRight size={15}/></button>
          <small>{data.meta.year}년 · 한국환경공단 · 유사시설 중앙값 비교 · 절감 가능량 아님</small>
        </article>}
        <article>
          <span className="simple-card-step">③ 수질을 지키며 실험하기</span>
          <h3>전력을 줄이면 탄소는 얼마나?</h3>
          <strong>{fmt(scenario.carbon, 0)}<small>tCO₂eq</small></strong>
          <div className="simple-scenario-bar" role="img" aria-label="대구 전체 전력 사용량을 10% 줄인다고 가정"><span/></div>
          <div className="simple-scenario-label"><span>절감 가정 10%</span><span>남는 사용량 90%</span></div>
          <p>대구 전체 시설의 전력을 10% 줄인다고 가정했을 때의 연간 간접배출 감소량입니다. 실제 절감률과 방류수질은 현장 실험으로 확인해야 합니다.</p>
          <button onClick={() => go('carbon')}>다른 절감률 계산 <ArrowUpRight size={15}/></button>
          <small>{data.meta.year}년 전력 {fmt(city.electricity_kwh / 1e6, 1)} GWh × GIR 공식 계수 · 가정 시나리오</small>
        </article>
      </div>
    </section>

    <section className="simple-next"><div><span className="eyebrow">그래서 대구에서 할 일</span><h2>공정별 계측 → 차이의 원인 확인 → 수질 유지 실증</h2><p>공공데이터는 조사 순서를 정합니다. 실제 감축 성과는 현장에서 검증합니다.</p></div><button className="button secondary" onClick={() => go('policy')}>실행 순서 보기 <ArrowRight size={16}/></button></section>
    <Source data={data}/>
  </>;
}
