import { useMemo, useState } from 'react';
import { Search, SlidersHorizontal } from 'lucide-react';
import type { Analysis, Facility } from './types';
import { DownloadLink, Empty, FacilityTable, fmt, Panel, Source, Takeaway } from './components';
import { BenchmarkScatter, MethodBars, RelationshipScatter } from './charts';
import OperationalWater from './OperationalWater';

const scales = ['소규모 <500', '중소 500–1만', '중형 1만–10만', '대형 ≥10만'];
type Metric = 'kwh_m3' | 'kwh_kg_bod';

export default function Benchmark({ data, onSelect }: { data: Analysis; onSelect: (facility: Facility) => void }) {
  const [scale, setScale] = useState('전체 규모');
  const [method, setMethod] = useState('전체 공법');
  const [search, setSearch] = useState('');
  const [metric, setMetric] = useState<Metric>('kwh_m3');
  const [screen, setScreen] = useState(true);
  const [sort, setSort] = useState('원단위 오름차순');
  const methods = useMemo(() => [...new Set(data.facilities.map(row => row.process_key))].filter(Boolean).sort(), [data.facilities]);
  const passes = (row: Facility) => (scale === '전체 규모' || row.scale === scale)
    && (method === '전체 공법' || row.process_key === method)
    && (!screen || row.benchmark_eligible);
  const national = data.national.filter(row => row.region !== '대구광역시' && passes(row));
  const daegu = data.facilities.filter(passes);
  const tableRows = daegu.filter(row => !search || `${row.name} ${row.district}`.includes(search));
  const rows = tableRows.toSorted((a, b) => sort === '전력량 내림차순'
    ? (b.electricity_kwh ?? 0) - (a.electricity_kwh ?? 0)
    : (a[metric] ?? Infinity) - (b[metric] ?? Infinity));
  const methodRows = data.method_comparison.filter(row => method === '전체 공법' || row.method === method);
  const small = data.scale_comparison[0];
  const large = data.scale_comparison.at(-1);
  const scaleRatio = small?.national_median != null && large?.national_median ? small.national_median / large.national_median : null;

  return <>
    <section className="benchmark-lead" aria-label="규모별 비교 핵심 발견">
      <div><span className="eyebrow">READ THE CHART FIRST</span><h2>시설 크기를 맞추면<br/>비교의 의미가 달라집니다.</h2></div>
      <div className="benchmark-lead-value"><strong>{fmt(scaleRatio, 1)}<small>배</small></strong><p>전국 소규모와 대형 시설의<br/>전력 원단위 중앙값 차이</p></div>
      <p className="benchmark-lead-foot">{data.meta.year}년 · 한국환경공단 · 소규모 {fmt(small?.national_median, 3)} vs 대형 {fmt(large?.national_median, 3)} kWh/m³. 규모별 관찰이며 규모의 인과효과는 아닙니다.</p>
    </section>

    <div className="filter-bar"><span className="filter-title"><SlidersHorizontal size={16}/>비교 조건</span><label><span className="sr-only">시설 규모</span><select value={scale} onChange={event => setScale(event.target.value)}><option>전체 규모</option>{scales.map(value => <option key={value}>{value}</option>)}</select></label><label><span className="sr-only">처리공법</span><select value={method} onChange={event => setMethod(event.target.value)}><option>전체 공법</option>{methods.map(value => <option key={value}>{value}</option>)}</select></label><label className="check"><input type="checkbox" checked={screen} onChange={event => setScreen(event.target.checked)}/>품질 검토 통과 시설만</label><button className="text-button" onClick={() => { setScale('전체 규모'); setMethod('전체 공법'); setScreen(true); setSearch(''); }}>초기화</button></div>

    <div className="grid-main">
      <Panel title="규모에 따라 대구의 위치를 살펴보세요" subtitle={`${data.meta.year}년 · 현재 조건: 타 지역 ${national.length}개 / 대구 ${daegu.length}개`} action={<label><span className="sr-only">산점도 전력 지표</span><select className="small-select" value={metric} onChange={event => setMetric(event.target.value as Metric)}><option value="kwh_m3">kWh/m³</option><option value="kwh_kg_bod">kWh/kg-BOD</option></select></label>}>
        <div className="chart-legend"><span><i className="dot national"/>전국 타 지역</span><span><i className="dot daegu"/>대구</span></div>
        {national.length || daegu.length ? <BenchmarkScatter national={national} daegu={daegu} metric={metric}/> : <Empty title="표시 가능한 시설이 없습니다">필터를 변경해 주세요.</Empty>}
        <Takeaway source={`${data.meta.year}년 · 한국환경공단 · x: m³/일, y: ${metric === 'kwh_m3' ? 'kWh/m³' : 'kWh/kg-BOD 근사'} · 양축 로그`}>청록색 점을 같은 유입량 범위의 회색 점과 비교하세요. 위쪽에 있는 점은 해당 지표가 높지만, 공법과 오염부하 확인 전에는 비효율로 단정할 수 없습니다.</Takeaway>
      </Panel>
      <Panel title="처리공법별 전력 분포" subtitle={`${data.meta.year}년 · 전국 적격 시설 · 공법별 n≥5 · 표본 수 상위 10개`}>
        <MethodBars rows={methodRows}/>
        <Takeaway source={`${data.meta.year}년 · 한국환경공단 · 중앙값 kWh/m³`}>막대는 공법별 전력 원단위의 중앙값입니다. 공법마다 시설 규모와 수질 조건이 섞여 있어 공법 자체의 절감 효과로 읽을 수 없습니다.</Takeaway>
      </Panel>
    </div>

    <div className="grid-two">
      <Panel title="큰 시설은 전력 총량도 큰가" subtitle={`${data.meta.year}년 · 시설용량 m³/일 × 연간 총전력 kWh`}>
        <RelationshipScatter national={national} daegu={daegu} kind="scale"/>
        <Takeaway source={`${data.meta.year}년 · 한국환경공단 · 전체 적격 표본 Spearman ρ=${fmt(data.correlations.electricity_kwh.capacity_m3_day, 3)}`}>시설용량과 전력 총량에는 강한 양의 순위상관이 있습니다. 총전력만으로 시설을 줄 세우면 규모의 영향을 효율 차이로 오해할 수 있습니다.</Takeaway>
      </Panel>
      <Panel title="수질 정화와 에너지는 함께 움직이나" subtitle={`${data.meta.year}년 · BOD 농도 제거율 % × 전력 원단위 kWh/m³`}>
        <RelationshipScatter national={national} daegu={daegu} kind="water"/>
        <Takeaway source={`${data.meta.year}년 · 한국환경공단 · 전체 적격 표본 Spearman ρ=${fmt(data.correlations.kwh_m3.bod_removal_pct, 3)}`}>전체 표본에서는 두 지표의 단순 순위상관이 거의 없습니다. 이 결과만으로 수질을 유지하며 전력을 줄일 수 있다고 판단할 수는 없습니다.</Takeaway>
      </Panel>
    </div>

    <Panel title="규모별 기준을 나눠서 보기" subtitle={`${data.meta.year}년 · 품질 검토 통과 표본 · 중앙값 kWh/m³`}>
      <div className="scale-grid">{data.scale_comparison.map(row => <div key={row.scale}><span>{row.scale}<small> m³/일</small></span><strong>{fmt(row.daegu_median, 3)}<small>대구 중앙값 · n={row.daegu_n}</small></strong><p>전국 {fmt(row.national_median, 3)} · n={row.national_n}</p></div>)}</div>
      <Takeaway>같은 규모 안에서 대구와 전국 중앙값을 비교하세요. 대구 중소·중형은 각각 {data.scale_comparison[1]?.daegu_n ?? 0}개·{data.scale_comparison[2]?.daegu_n ?? 0}개로 표본이 작아 순위 해석을 보류해야 합니다.</Takeaway>
    </Panel>

    <Panel title="시설별 상세 수치" subtitle={`${data.meta.year}년 · 대구 · 유량당 전력과 BOD 제거율을 함께 확인`} action={<DownloadLink file="daegu_2025.csv"/>}>
      <Takeaway>‘유사시설 대비’가 1배를 넘으면 비교집단 중앙값보다 전력 원단위가 높다는 뜻입니다. 이는 달성 가능한 절감률이나 비효율 판정이 아닙니다.</Takeaway>
      <details className="data-details"><summary>시설 검색 및 전체 표 보기</summary><div className="table-controls"><label className="search"><Search size={16}/><input placeholder="시설명 또는 구군 검색" aria-label="시설명 또는 구군 검색" value={search} onChange={event => setSearch(event.target.value)}/></label><label><span className="sr-only">시설 정렬</span><select value={sort} onChange={event => setSort(event.target.value)}><option>원단위 오름차순</option><option>전력량 내림차순</option></select></label></div><FacilityTable rows={rows} data={data} onSelect={onSelect}/></details>
    </Panel>

    {data.operational_api?.available && <OperationalWater api={data.operational_api}/>}
    <Panel title="같은 시설의 연도별 변화" subtitle={`2024 → 2025년 · 주소와 시설명이 일치하는 ${data.trends.length}개`}>
      <Takeaway>원단위의 연도별 변화와 총전력 변화율은 서로 다른 값입니다. 처리량과 운영 조건이 달라질 수 있어 변화 자체를 개선 효과로 해석하지 않습니다.</Takeaway>
      <details className="data-details"><summary>{data.trends.length}개 시설의 2024–2025년 표 보기</summary><div className="table-wrap" tabIndex={0} role="region" aria-label="동일 시설 연도별 변화 표"><table><thead><tr><th>시설명</th><th>2024 kWh/m³</th><th>2025 kWh/m³</th><th>연간 전력 변화 %</th></tr></thead><tbody>{data.trends.map(row => <tr key={row.facility_id}><td>{row.name}</td><td>{fmt(row.intensity_previous, 3)}</td><td>{fmt(row.intensity_current, 3)}</td><td>{fmt(row.energy_change_pct, 1)}%</td></tr>)}</tbody></table></div></details>
    </Panel>
    <Source data={data}/>
  </>;
}
