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
  const rankFacility = data.facilities.find(facility => facility.name === '다사 달천');
  const scenario = calculateScenario(city.electricity_kwh, 10, data.meta.factor.value);

  return <>
    <section className="simple-hero" aria-labelledby="simple-hero-title">
      <div className="simple-hero-copy">
        <span className="eyebrow">{data.meta.year} · 대구 공공하수처리시설 {city.n}곳</span>
        <h2 id="simple-hero-title">대구 하수시설 전력,<br/><em>5곳에 집중됩니다.</em></h2>
        <p>대구 전체 전력을 줄일 여지를 찾으려면 전력이 모이는 곳부터 공정별 사용량을 확인해야 합니다.</p>
        <button className="button primary" onClick={() => go('benchmark')}>시설 비교 보기 <ArrowRight size={16}/></button>
      </div>
      <div className="simple-hero-number">
        <strong>{fmt(share, 1)}<small>%</small></strong>
        <p>전력 사용 상위 5곳의 비중</p>
        <div className="simple-share" role="img" aria-label={'대구 상위 5개 시설의 전력 비중 ' + fmt(share, 1) + '%'}><span style={{ width: String(share) + '%' }}/></div>
        <div className="simple-share-label"><span>상위 5곳</span><span>나머지 {city.n - topFive.length}곳</span></div>
        <small>{topFive.map(facility => facility.name).join(' · ')}</small>
      </div>
    </section>
    <p className="simple-boundary">전력량이 크다고 비효율이라는 뜻은 아닙니다. {data.meta.year}년 한국환경공단 시설별 연간 총전력 합계입니다.</p>

    <div className="simple-stats" aria-label="대구의 관측 전력과 간접배출 추정">
      <div><span>대구 시설</span><strong>{city.n}<small>곳</small></strong></div>
      <div><span>연간 전력 사용</span><strong>{fmt(city.electricity_kwh / 1e6, 1)}<small>GWh</small></strong></div>
      <div><span>전력 간접배출 추정</span><strong>{fmt(city.indirect_tco2e_est / 1000, 1)}<small>천 tCO₂eq</small></strong></div>
    </div>
    <p className="simple-boundary">간접배출은 관측 전력 × GIR 공식 계수로 환산했습니다. 시설 전체 온실가스 배출량은 아닙니다.</p>

    <section className="simple-discoveries" aria-labelledby="simple-discoveries-title">
      <div className="simple-section-title"><span className="eyebrow">NEXT THREE QUESTIONS</span><h2 id="simple-discoveries-title">그다음 살펴볼 세 가지</h2></div>
      <div className="simple-cards">
        {peer?.available && peerFacility && <article>
          <span className="simple-card-step">01 · 어디를 더 진단할까?</span>
          <strong>{fmt(peer.ratio, 2)}<small>배</small></strong>
          <h3>유사시설과의 차이</h3>
          <p>{peerFacility.name}의 하수 1m³당 전력은 비슷한 타 지역 시설 {peer.count}곳의 중앙값보다 높습니다. 절감 가능량을 뜻하지는 않습니다.</p>
          <button onClick={() => onSelect(peerFacility)}>비교 대상 보기 <ArrowUpRight size={15}/></button>
          <small>{data.meta.year}년 · 한국환경공단 · 규모·공법·BOD 부하 비교</small>
        </article>}
        {rankFacility && <article>
          <span className="simple-card-step">02 · 무엇을 기준으로 볼까?</span>
          <strong>{fmt(rankFacility.rank_volume, 0)}<small>위</small> <span>→</span> {fmt(rankFacility.rank_bod, 0)}<small>위</small></strong>
          <h3>지표에 따라 달라지는 순위</h3>
          <p>{rankFacility.name}은 하수량당 전력과 BOD 제거량당 전력의 순위가 다릅니다. 처리한 물과 제거한 오염을 함께 봐야 합니다.</p>
          <button onClick={() => onSelect(rankFacility)}>시설 수치 보기 <ArrowUpRight size={15}/></button>
          <small>{data.meta.year}년 · 대구 {city.n}곳 내 순위 · BOD 제거량은 근사</small>
        </article>}
        <article>
          <span className="simple-card-step">03 · 감축 규모는 얼마일까?</span>
          <strong>{fmt(scenario.carbon, 0)}<small>tCO₂eq</small></strong>
          <h3>전력 10% 절감 가정</h3>
          <p>대구 전체 전력을 10% 줄인다고 가정할 때의 간접배출 감축 잠재량입니다. 현장에서 검증된 성과는 아닙니다.</p>
          <button onClick={() => go('carbon')}>절감률 바꿔 보기 <ArrowUpRight size={15}/></button>
          <small>{data.meta.year}년 전력 · GIR 계수 0.4330 tCO₂eq/MWh</small>
        </article>
      </div>
    </section>

    <section className="simple-next"><div><span className="eyebrow">FROM DATA TO ACTION</span><h2>계측 → 원인 확인 → 수질 유지 실증</h2><p>공공데이터는 현장에서 확인할 순서를 정하는 데 사용합니다.</p></div><button className="button secondary" onClick={() => go('policy')}>대구 실행 제안 <ArrowRight size={16}/></button></section>
    <Source data={data}/>
  </>;
}
