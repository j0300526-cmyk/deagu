import { ArrowRight, ArrowUpRight, Check, Database, Droplets, FileText } from 'lucide-react';
import type { Analysis, Facility } from './types';
import { DownloadLink, FacilityTable, fmt, Panel, Source } from './components';
import { BenchmarkScatter, FacilityBars } from './charts';

type Props = { data: Analysis; onSelect: (f: Facility) => void; go: (page: string) => void };

export default function Overview({ data, onSelect, go }: Props) {
  const s = data.summary.daegu;
  const n = data.summary.national;
  const major = data.facilities.filter(f => f.capacity_m3_day >= 500).toSorted((a, b) => (a.kwh_m3 ?? Infinity) - (b.kwh_m3 ?? Infinity));
  const top = data.facilities.toSorted((a, b) => (b.electricity_kwh ?? 0) - (a.electricity_kwh ?? 0)).slice(0, 5);
  const share = top.reduce((sum, f) => sum + (f.electricity_kwh ?? 0), 0) / s.electricity_kwh * 100;
  const compared = Object.values(data.peers).filter(p => p.available).length;
  const maxIntensity = Math.max(s.weighted_kwh_m3, n.weighted_kwh_m3);

  return <>
    <div className="overview-bento">
      <section className="bento-card lead-discovery" aria-labelledby="discovery-title">
        <div className="card-kicker"><span>KEY FINDING / 01</span><span>ENERGY INTENSITY</span></div>
        <h2 id="discovery-title">시설 평균과 도시 전체 효율은<br/>서로 다른 모습을 보여줍니다.</h2>
        <div className="lead-stat"><span className="lead-stat-label">대구의 유입량 가중 전력 원단위</span><strong>{fmt(s.weighted_kwh_m3, 3)}<span>kWh/m³</span></strong></div>
        <div className="intensity-comparison" role="img" aria-label={`2025년 유입량 가중 전력 원단위: 대구 ${fmt(s.weighted_kwh_m3, 3)}, 전국 ${fmt(n.weighted_kwh_m3, 3)} kWh/m³`}>
          {[{ label: '대구', value: s.weighted_kwh_m3, cls: 'daegu' }, { label: '전국', value: n.weighted_kwh_m3, cls: 'nation' }].map(r => <div className="intensity-row" key={r.label}><span>{r.label}</span><div><i className={r.cls} style={{ width: `${r.value / maxIntensity * 100}%` }}/></div><b>{fmt(r.value, 3)}</b></div>)}
        </div>
        <div className="lead-explanation"><p>대구 시설별 단순 평균은 <b>{fmt(s.mean_kwh_m3, 3)} kWh/m³</b>.<br/>유량을 반영하면 도시 전체의 에너지 효율을 다르게 읽게 됩니다.</p><button className="round-link" aria-label="전국 에너지 비교로 이동" onClick={() => go('benchmark')}><ArrowUpRight size={22}/></button></div>
        <p className="data-stamp">{data.meta.year}년 · 한국환경공단 · 전력 합계 / 연간 환산 유입량 합계<br/>지역별 규모·공법 구성 차이를 포함한 기술통계입니다.</p>
      </section>

      <section className="bento-card scope-card" aria-labelledby="scope-title"><div className="card-kicker"><span>THE RESEARCH SCOPE</span><Database size={18}/></div><h2 id="scope-title">전국을 기준으로,<br/>대구를 자세히.</h2><div className="scope-figures"><div><strong>{s.n}<small>개소</small></strong><span>대구 하수처리시설</span></div><div><strong>{fmt(n.n, 0)}<small>개소</small></strong><span>전국 비교 데이터</span></div></div><div className="scope-foot"><span><Check size={14}/>공식 2025 통계와 전수 대조</span><a href="#quality" aria-label="원본 검증 방법 보기"><ArrowUpRight size={17}/></a></div></section>

      <section className="bento-card concentration-card" aria-labelledby="concentration-title"><div className="card-kicker"><span>KEY FINDING / 02</span><span>ANNUAL ELECTRICITY</span></div><h2 id="concentration-title">전력 사용은<br/>어디에 집중되는가.</h2><div className="concentration-stat"><strong>{fmt(share, 1)}<small>%</small></strong><p>전력 사용 상위 5개 시설의<br/>대구 전체 전력량 대비 비중</p></div><div className="share-bar" role="img" aria-label={`상위 5개 시설 ${fmt(share, 1)}%, 나머지 ${fmt(100 - share, 1)}%`}><span style={{ width: `${share}%` }}/></div><div className="share-caption"><span>상위 5개</span><span>나머지 {s.n - top.length}개</span></div><p className="data-stamp">{data.meta.year}년 · 한국환경공단 · 대구 총 {fmt(s.electricity_kwh / 1e6, 2)} GWh/년</p></section>

      <Panel title="대구 주요 시설의 전력 원단위" subtitle={`${data.meta.year}년 · 대구 시설용량 500 m³/일 이상 ${major.length}개 · 유입량당 전력 kWh/m³`} className="bento-major" action={<button className="text-button" onClick={() => go('benchmark')}>상세 비교<ArrowUpRight size={16}/></button>}><FacilityBars rows={major}/><div className="figure-note"><span className="figure-number">FIG. 01</span><p>규모·부하 보정 전 지표입니다. 전력량의 크기만으로 시설의 비효율을 판단하지 않습니다.</p></div></Panel>

      <section className="bento-card water-card" aria-labelledby="water-title"><div className="card-kicker"><span>WATER QUALITY</span><Droplets size={20}/></div><h2 id="water-title">에너지를 읽을 때,<br/>정화 성능도 함께.</h2><div className="water-value">{fmt(s.median_bod_removal_pct, 1)}<small>%</small></div><p className="water-value-caption">대구 BOD 농도 제거율 중앙값</p><div className="water-notes"><p>수질 성능을 유지하는 조건에서<br/>에너지 개선의 여지를 살펴봅니다.</p><p>농도 제거율은 법정 방류수 기준<br/>충족 여부와 구분해야 합니다.</p></div><p className="data-stamp">{data.meta.year}년 · 한국환경공단 · 유입·방류 BOD 기반</p></section>

      <Panel title="전국의 분포 안에서 대구의 위치를 읽다" subtitle={`${data.meta.year}년 · 일평균 유입량 m³/일 × 전력 원단위 kWh/m³ · 양축 로그`} className="bento-distribution"><div className="chart-legend"><span><i className="dot national"/>전국 타 지역</span><span><i className="dot daegu"/>대구</span></div><BenchmarkScatter national={data.national.filter(f => f.region !== '대구광역시' && f.benchmark_eligible)} daegu={data.facilities.filter(f => f.benchmark_eligible)}/><div className="figure-note"><span className="figure-number">FIG. 02</span><p>품질 검토를 통과한 시설을 표시합니다. 규모와 공법의 구성 차이를 고려해 해석해야 합니다.</p></div></Panel>

      <aside className="bento-card research-reading"><div className="card-kicker"><span>HOW TO READ THIS STUDY</span><span>↘</span></div><h2>비교의 기준을<br/>먼저 확인하세요.</h2><p>같은 공법, 유사한 규모와 BOD 부하.<br/>비교 조건을 만족할 때만<br/>상대 효율을 제시합니다.</p><dl><div><dt>유사시설 비교 가능</dt><dd>{compared}<small> / {s.n}개</small></dd></div><div><dt>동일 시설 전년 비교</dt><dd>{data.trends.length}<small>개</small></dd></div><div><dt>검증된 시설 좌표</dt><dd>{data.coordinates.length}<small>개</small></dd></div></dl><button className="text-button" onClick={() => go('quality')}>출처와 분석 한계 읽기<ArrowRight size={17}/></button></aside>
    </div>

    <div className="editorial-section-heading"><span className="eyebrow">RESEARCH FINDINGS</span><h2>숫자가 가리키는 세 가지 질문</h2><p>데이터의 관찰에서 현장 진단의 질문으로 이어갑니다.</p></div>
    <div className="findings-grid">{data.insights.slice(1, 4).map((x, i) => <button key={x.title} className="finding-card" onClick={() => go('policy')}><span className="finding-card-top"><span>0{i + 1}</span><ArrowUpRight size={20}/></span><strong>{x.value}<small>{x.unit}</small></strong><h3>{x.title}</h3><p>{x.limitation}</p><span className="data-stamp">{x.year}년 · 한국환경공단 · 정책 제안에서 근거 확인</span></button>)}</div>

    <Panel title="전력 사용 상위 시설의 운영 지표" subtitle={`${data.meta.year}년 · 대구 · 총량 순서는 비효율 순위가 아닙니다`} action={<DownloadLink file="daegu_2025.csv"/>}><FacilityTable rows={top} data={data} onSelect={onSelect} compact/></Panel>
    <div className="overview-report"><FileText size={25}/><div><span className="eyebrow">OPEN RESEARCH</span><h2>발견의 근거를, 누구나 확인할 수 있도록.</h2><p>계산식·검증 절차·정책적 한계를 보고서와 원본 기록에 함께 담았습니다.</p></div><a className="button primary" href="/downloads/ANALYSIS_REPORT.md" download>연구보고서 받기<ArrowUpRight size={16}/></a></div>
    <Source data={data}/>
  </>;
}
