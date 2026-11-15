import { lazy, Suspense, useEffect, useRef, useState } from 'react';
import { ArrowDown, ArrowUpRight, Database, Download, Menu, X } from 'lucide-react';
import type { Analysis, Facility } from './types';
import { FacilityDetail, fmt } from './components';
import { AIInsights, Benchmark, CarbonSimulator, DataQuality, Overview, PolicyInsights } from './pages';

const FacilityMap = lazy(() => import('./FacilityMap'));
const navigation = [
  { id: 'overview', label: '핵심 발견', ko: 'OVERVIEW' },
  { id: 'map', label: '시설 찾기', ko: 'MAP' },
  { id: 'benchmark', label: '전국과 비교', ko: 'BENCHMARK' },
  { id: 'ai', label: 'AI로 살펴보기', ko: 'AI INSIGHTS' },
  { id: 'carbon', label: '탄소 계산', ko: 'SCENARIO' },
  { id: 'policy', label: '실행 제안', ko: 'POLICY' },
];
const pageContent: Record<string, { title: string; description: string; kicker: string }> = {
  overview: { title: '대구 하수처리시설의 숨은 탄소격차', description: '전력이 어디에 집중되고, 어떤 시설을 더 살펴봐야 하는지 공공데이터로 찾았습니다.', kicker: '01 / 핵심 발견' },
  map: { title: '대구의 시설은 어디에 있나?', description: '시설을 선택해 전력 사용과 수질을 확인하세요. 지도점은 주소 기반 추정 위치이며 시설 부지 좌표가 아닙니다.', kicker: '02 / 시설 지도' },
  benchmark: { title: '비슷한 시설과 비교하면 어떤가?', description: '시설 크기와 처리조건이 다르면 전력량도 달라집니다. 비교 조건을 맞춰 대구의 위치를 살펴봅니다.', kicker: '03 / 전국 비교' },
  ai: { title: '전력 차이와 관련된 조건은?', description: 'AI가 예측에 사용한 주요 조건과 대구 시설에서의 예측 오차를 보여줍니다.', kicker: '04 / AI 분석' },
  carbon: { title: '전력을 줄이면 탄소는 얼마나?', description: '원하는 절감률을 넣어 가정상 감축 잠재량을 계산해 보세요. 실증된 효과는 아닙니다.', kicker: '05 / 탄소 시나리오' },
  policy: { title: '대구는 무엇부터 실행할까?', description: '데이터의 발견을 계측, 원인 진단, 수질 유지 실증으로 연결합니다.', kicker: '06 / 실행 제안' },
  quality: { title: '이 숫자는 어디서 왔나?', description: '공식 자료, 분석연도, 결측률과 계산 방법을 확인할 수 있습니다.', kicker: '자료와 방법' },
};
function route() { const id = window.location.hash.slice(1); return Object.hasOwn(pageContent, id) ? id : 'overview'; }

export default function App() {
  const [data, setData] = useState<Analysis | null>(null);
  const [error, setError] = useState('');
  const [page, setPage] = useState(route);
  const [mobile, setMobile] = useState(false);
  const menuButton = useRef<HTMLButtonElement>(null);
  const [selected, setSelected] = useState<Facility | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    fetch('/data/analysis.json', { signal: controller.signal })
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); }).then(setData)
      .catch(e => { if (e.name !== 'AbortError') setError(String(e)); });
    return () => controller.abort();
  }, []);
  useEffect(() => {
    const onRoute = () => { setPage(route()); setMobile(false); setSelected(null); window.scrollTo(0, 0); };
    window.addEventListener('hashchange', onRoute);
    return () => window.removeEventListener('hashchange', onRoute);
  }, []);
  useEffect(() => {
    if (!mobile) return;
    const onEscape = (e: KeyboardEvent) => { if (e.key === 'Escape') { setMobile(false); menuButton.current?.focus(); } };
    window.addEventListener('keydown', onEscape);
    return () => window.removeEventListener('keydown', onEscape);
  }, [mobile]);
  const go = (id: string) => { window.location.hash = id; setMobile(false); if (id === page) window.scrollTo({ top: 0, behavior: 'smooth' }); };
  if (error) return <div className="load-state"><Database size={32}/><h1>분석 결과를 불러오지 못했습니다.</h1><p>{error}</p><button className="button primary" onClick={() => location.reload()}>다시 불러오기</button></div>;
  if (!data) return <div className="load-state"><span className="lab-mark">D<span>c</span></span><h1>DAEGU CARBON LAB</h1><p>공식 데이터에서 연구 결과를 불러옵니다.</p></div>;
  const props = { data, onSelect: setSelected, go };
  const content = pageContent[page];
  return <div className={`app page-${page}`}>
    <a href="#main-content" className="skip-link" onClick={e => { e.preventDefault(); document.getElementById('main-content')?.focus(); }}>본문 바로가기</a>
    <header className="site-header"><div className="masthead">
      <a className="brand" href="#overview" aria-label="DAEGU CARBON LAB 연구 개요"><span className="lab-mark" aria-hidden="true">D<span>c</span></span><span className="brand-name">DAEGU<br/>CARBON LAB<span className="brand-description">PUBLIC DATA RESEARCH</span></span></a>
      <div className="masthead-note">도시의 환경을 읽는<br/><strong>공공데이터 연구 노트</strong></div>
      <div className="masthead-actions"><a href="#quality" className="methods-link" aria-current={page === 'quality' ? 'page' : undefined}>데이터·방법론<ArrowUpRight size={15}/></a><a href="/downloads/ANALYSIS_REPORT.md" download className="button report-button"><Download size={15}/>연구보고서</a><button ref={menuButton} className="mobile-toggle icon-button" aria-label={mobile ? '분석 메뉴 닫기' : '분석 메뉴 열기'} aria-expanded={mobile} aria-controls="primary-navigation" onClick={() => setMobile(v => !v)}>{mobile ? <X/> : <Menu/>}</button></div>
    </div><nav id="primary-navigation" className={`primary-navigation ${mobile ? 'is-open' : ''}`} aria-label="주요 분석 메뉴">{navigation.map((n, i) => <a key={n.id} href={`#${n.id}`} className={`nav-link ${page === n.id ? 'active' : ''}`} aria-current={page === n.id ? 'page' : undefined} onClick={() => setMobile(false)}><span className="nav-index">0{i + 1}</span><span className="nav-copy"><strong>{n.label}</strong><small>{n.ko}</small></span><ArrowUpRight className="nav-arrow" size={15}/></a>)}</nav></header>

    <main id="main-content" tabIndex={-1}>
      <div className="page-heading"><div className="page-heading-content"><div className="eyebrow">{content.kicker}<span>DAEGU · SOUTH KOREA</span></div><h1>{page === 'overview' ? <>대구 하수처리시설의<br/><em>숨은 탄소격차</em></> : content.title}</h1><p>{content.description}</p></div><aside className="research-meta" aria-label="분석 기준"><span className="edition-label">DATA EDITION</span><strong>{data.meta.year}<small>관측연도</small></strong><dl><div><dt>분석 범위</dt><dd>전국 {fmt(data.summary.national.n, 0)} · 대구 {data.summary.daegu.n}개</dd></div><div><dt>비교연도</dt><dd>{data.meta.previous_year} → {data.meta.year}</dd></div><div><dt>데이터 검증</dt><dd>{data.meta.verified_on.replaceAll('-', '.')}</dd></div></dl></aside></div>
      <div className="context-strip"><span><i/>공식 공공데이터 기반 연구</span><a href="#quality">출처·계산식·단위 확인<ArrowUpRight size={13}/></a><span className="context-unit">관측 · 근사 · AI 예측 · 가정 시나리오를 구분합니다</span></div>
      <div className="page-content" key={page}>{page === 'overview' ? <Overview {...props}/> : page === 'benchmark' ? <Benchmark {...props}/> : page === 'ai' ? <AIInsights {...props}/> : page === 'carbon' ? <CarbonSimulator {...props}/> : page === 'policy' ? <PolicyInsights {...props}/> : page === 'quality' ? <DataQuality {...props}/> : <Suspense fallback={<div className="panel empty">시설 지도를 불러오고 있습니다.</div>}><FacilityMap {...props}/></Suspense>}</div>
      <div className="research-endnote"><span>RESEARCH NOTE / 2026</span><p>측정값을 근거로, 도시의 다음 선택을 생각합니다.</p><a href="#quality">분석의 범위와 한계 읽기<ArrowUpRight size={16}/></a></div>
      <footer><div><strong>DAEGU CARBON LAB</strong><span>2026 대구광역시 기후·환경·탄소중립 공공데이터 AI 활용대회</span></div><button onClick={() => { window.scrollTo({ top: 0, behavior: 'smooth' }); }} className="back-top">맨 위로<ArrowDown size={14}/></button></footer>
    </main>
    {selected && <FacilityDetail key={selected.facility_id} facility={selected} data={data} onClose={() => setSelected(null)}/>}
  </div>;
}
