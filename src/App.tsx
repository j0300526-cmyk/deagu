import { lazy, Suspense, useEffect, useRef, useState } from 'react';
import { ArrowDown, ArrowUpRight, Database, Download, Menu, X } from 'lucide-react';
import type { Analysis, Facility } from './types';
import { FacilityDetail, fmt } from './components';
import { AIInsights, Benchmark, CarbonSimulator, DataQuality, Overview, PolicyInsights } from './pages';

const FacilityMap = lazy(() => import('./FacilityMap'));
const navigation = [
  { id: 'overview', label: 'Overview', ko: '연구 개요' },
  { id: 'map', label: 'Facility Map', ko: '시설 지도' },
  { id: 'benchmark', label: 'Benchmark', ko: '에너지 비교' },
  { id: 'ai', label: 'AI Insights', ko: '모델 분석' },
  { id: 'carbon', label: 'Carbon Simulator', ko: '탄소 시나리오' },
  { id: 'policy', label: 'Policy Insights', ko: '정책 제안' },
];
const pageContent: Record<string, { title: string; description: string; kicker: string }> = {
  overview: { title: '대구 하수처리시설의 숨은 탄소격차', description: '공공데이터로 읽는 수질 정화 성능, 에너지 효율, 그리고 전력 간접배출의 관계.', kicker: '01 / RESEARCH OVERVIEW' },
  map: { title: '시설의 위치와 운영의 맥락', description: '검증된 좌표와 실제 운영 지표를 연결합니다. 확인되지 않은 위치는 지도에 표시하지 않습니다.', kicker: '02 / FACILITY ATLAS' },
  benchmark: { title: '에너지 효율, 비교의 조건을 묻다', description: '시설 규모·처리공법·오염부하를 함께 고려해 전국 유사시설과 대구를 비교합니다.', kicker: '03 / ENERGY BENCHMARK' },
  ai: { title: '모델이 설명하는 에너지의 차이', description: '대구를 학습에서 제외한 독립 평가. XGBoost 예측과 SHAP 기여도, 기준모델과의 성능 차이를 공개합니다.', kicker: '04 / XGBOOST & SHAP' },
  carbon: { title: '전력 절감에서 탄소 시나리오까지', description: '2025년 전력사용량에 가정 절감률을 적용합니다. 실증된 감축 효과와 구분해 살펴보세요.', kicker: '05 / CARBON SCENARIOS' },
  policy: { title: '데이터를 정책의 근거로', description: '실제 수치와 비교 기준에서 출발해, 현장에서 검증해야 할 정책의 질문을 제안합니다.', kicker: '06 / POLICY & IMPLICATIONS' },
  quality: { title: '분석의 근거를 열어두다', description: '공식 출처, 결측률, 계산식과 검증 절차. 연구 결과를 재현하는 데 필요한 기록입니다.', kicker: 'RESEARCH / DATA & METHODS' },
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
