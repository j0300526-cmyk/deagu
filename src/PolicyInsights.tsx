import { ArrowRight, ArrowUpRight, Database, Download, Droplets, Search } from 'lucide-react';
import type { Analysis } from './types';
import { DownloadLink, fmt, Source } from './components';

export default function PolicyInsights({ data, go }: { data: Analysis; go: (page: string) => void }) {
  const concentration = data.insights[1];
  const peer = data.insights[2];
  const ranking = data.insights[3];
  const carbon = data.insights[4];
  const steps = [
    { number: '01', icon: Database, title: '전력이 많이 쓰이는 곳부터 계측', question: '어디서 전기를 쓰는가?', evidence: concentration, result: '상위 5개 시설의 송풍·펌핑·슬러지 처리 전력을 공정별로 구분해 기록합니다.' },
    { number: '02', icon: Search, title: '비슷한 시설과 차이가 큰 곳을 진단', question: '왜 차이가 나는가?', evidence: peer, result: '전력계측 범위, 연계처리량, 유입수질과 방류 조건을 현장에서 확인합니다.' },
    { number: '03', icon: Droplets, title: '수질을 유지하며 작은 실험', question: '줄여도 물은 깨끗한가?', evidence: ranking, result: '유입량당 전력과 BOD 제거당 전력을 함께 보고, 방류수질을 추적합니다.' },
  ];

  return <>
    <section className="policy-story-intro">
      <span className="eyebrow">EVIDENCE → FIELD TEST → POLICY</span>
      <h2>대구에서 검증할 시설과 공정을<br/><em>데이터로 먼저 찾습니다.</em></h2>
      <p>공공데이터는 우선순위를 알려줍니다. 실제 절감률은 현장 계측, 운영조건 확인, 방류수질 실증을 거쳐 판단해야 합니다.</p>
    </section>

    <div className="policy-roadmap" aria-label="대구 하수처리시설 정책 실행 3단계">
      {steps.map(({ number, icon: Icon, title, question, evidence, result }) => <article key={number} className="policy-step">
        <div className="policy-step-top"><span>{number} / 03</span><Icon size={23} aria-hidden="true"/></div>
        <p className="policy-step-question">{question}</p>
        <h3>{title}</h3>
        <div className="policy-step-value"><strong>{evidence.value}</strong><small>{evidence.unit}</small></div>
        <p className="policy-step-meaning">{result}</p>
        <details><summary>수치의 근거와 한계</summary><p><b>관찰</b> {evidence.finding}</p><p><b>비교 기준</b> {evidence.comparison}</p><p><b>한계</b> {evidence.limitation}</p><p>출처: {evidence.source}</p></details>
      </article>)}
    </div>

    <section className="policy-carbon">
      <div><span className="eyebrow">POTENTIAL IMPACT / ASSUMPTION</span><h2>실증 후에야 탄소 감축량이 됩니다.</h2><p>2025년 대구 시설 총전력에서 일률적으로 10%를 줄인다고 가정하면 공식 전력배출계수로 환산한 수치입니다.</p><button className="story-inline-link" onClick={() => go('carbon')}>절감률을 바꿔 계산하기 <ArrowUpRight size={15}/></button></div>
      <div className="policy-carbon-number"><strong>{carbon.value}</strong><span>{carbon.unit}</span><small>가정 시나리오 · 시설 직접배출 및 현장 실현 가능성 미포함</small></div>
    </section>

    <div className="policy-briefing"><div><span className="eyebrow">READY FOR REVIEW</span><h2>근거를 다시 확인할 수 있습니다.</h2><p>분석 코드, 비교 기준, 결측률과 AI 활용 내용을 공개했습니다. 시민 설명에는 1페이지 인포그래픽을 사용할 수 있습니다.</p></div><div className="policy-briefing-actions"><a className="button primary" href="/downloads/daegu_carbon_lab_research_poster.pdf" download><Download size={15}/>1페이지 인포그래픽</a><DownloadLink file="ANALYSIS_REPORT.md" label="분석보고서"/></div></div>
    <p className="policy-source-line">{data.meta.year}년 · 한국환경공단 공공하수처리시설 현황 · 전국 {fmt(data.summary.national.n, 0)}개, 대구 {data.summary.daegu.n}개 · 탄소 환산: GIR 공식 계수</p>
    <button className="story-inline-link" onClick={() => go('benchmark')}>시설별 비교 근거 확인 <ArrowRight size={15}/></button>
    <Source data={data}/>
  </>;
}
