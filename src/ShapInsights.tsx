import { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { Analysis, ShapAnalysis, ShapPrediction } from './types';
import { DownloadLink, Empty, fmt, Note, Panel } from './components';

const tick = { fontSize: 11, fill: '#65786D' };
const positive = '#147D5A';
const negative = '#8B715A';
const signed = (value: number) => `${value > 0 ? '+' : ''}${fmt(value, 3)}`;

function GlobalImportance({ shap }: { shap: ShapAnalysis }) {
  return <div className="chart shap-chart" role="img" aria-label={`대구 ${shap.n}개 시설의 XGBoost 평균 절대 SHAP 값. 상세 수치는 아래 표에서 확인할 수 있습니다.`}>
    <ResponsiveContainer width="100%" height="100%">
      <BarChart layout="vertical" data={shap.importance} margin={{ top: 10, right: 22, left: 0, bottom: 15 }}>
        <CartesianGrid horizontal={false} stroke="#E4EADD" />
        <XAxis type="number" tick={tick} tickFormatter={value => fmt(value, 2)} axisLine={false} tickLine={false} />
        <YAxis type="category" dataKey="feature" width={122} tick={tick} axisLine={false} tickLine={false} />
        <Tooltip cursor={{ fill: '#EDF2E9' }} content={({ active, payload }) => {
          if (!active || !payload?.length) return null;
          const row = payload[0].payload as ShapAnalysis['importance'][number];
          return <div className="custom-tooltip"><strong>{row.feature}</strong><span>평균 |SHAP| {fmt(row.mean_abs, 4)}</span><span>log(kWh/m³) · 대구 {shap.n}개</span></div>;
        }} />
        <Bar dataKey="mean_abs" fill={positive} maxBarSize={19} radius={[0, 3, 3, 0]} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  </div>;
}

function LocalContributions({ row }: { row: ShapPrediction }) {
  return <div className="chart shap-chart" role="img" aria-label={`${row.name}의 변수별 SHAP 기여도. 양수는 모델 예측을 높이고 음수는 낮춥니다. 상세 수치는 아래 표에서 확인할 수 있습니다.`}>
    <ResponsiveContainer width="100%" height="100%">
      <BarChart layout="vertical" data={row.contributions} margin={{ top: 10, right: 22, left: 0, bottom: 15 }}>
        <CartesianGrid horizontal={false} stroke="#E4EADD" />
        <XAxis type="number" tick={tick} tickFormatter={value => signed(Number(value))} axisLine={false} tickLine={false} />
        <YAxis type="category" dataKey="feature" width={122} tick={tick} axisLine={false} tickLine={false} />
        <ReferenceLine x={0} stroke="#65786D" />
        <Tooltip cursor={{ fill: '#EDF2E9' }} content={({ active, payload }) => {
          if (!active || !payload?.length) return null;
          const entry = payload[0].payload as ShapPrediction['contributions'][number];
          return <div className="custom-tooltip"><strong>{entry.feature}</strong><span>입력값 {entry.value === null ? '결측 · 학습자료 기준 대치' : String(entry.value)}</span><b>SHAP {signed(entry.shap_value)} log(kWh/m³)</b></div>;
        }} />
        <Bar dataKey="shap_value" maxBarSize={19} isAnimationActive={false}>
          {row.contributions.map(entry => <Cell key={entry.key} fill={entry.shap_value >= 0 ? positive : negative} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  </div>;
}

export default function ShapInsights({ data }: { data: Analysis }) {
  const shap = data.model.shap;
  const [facilityId, setFacilityId] = useState('');
  if (!shap?.available || !shap.predictions.length) return <Panel title="XGBoost SHAP 분석" subtitle={`${data.meta.year}년 · 실제 계산 결과가 있는 경우에만 표시합니다`}>
    <Empty title="SHAP 결과를 표시할 수 없습니다">{shap?.reason ?? 'XGBoost 학습·SHAP 계산 결과가 아직 생성되지 않았습니다.'}</Empty>
  </Panel>;

  const row = shap.predictions.find(entry => entry.facility_id === facilityId) ?? shap.predictions[0];
  const actual = data.model.predictions.find(entry => entry.facility_id === row.facility_id)?.actual;
  const facilityIndex = shap.predictions.findIndex(entry => entry.facility_id === row.facility_id);
  const total = row.contributions.reduce((sum, entry) => sum + entry.shap_value, 0);
  const top = shap.importance[0];
  return <section className="shap-section" aria-labelledby="shap-heading">
    <div className="editorial-section-heading">
      <div><span className="eyebrow">INSIDE THE XGBOOST MODEL</span><h2 id="shap-heading">예측을 이루는 일곱 가지 단서</h2></div>
      <p>{data.meta.year}년 · {shap.model} · {shap.method}<br />대구 독립평가 {shap.n}개 시설의 실제 SHAP 계산</p>
    </div>
    <Note>이 설명은 <b>XGBoost 전용</b>입니다. 성능 기준 선택 모델은 {data.model.selected}입니다. SHAP은 학습된 모델 안에서의 기여도이며 원인·비효율 판정·달성 가능한 절감량을 뜻하지 않습니다.</Note>
    <div className="grid-two shap-grid">
      <Panel title="대구 예측에 영향을 준 변수" subtitle={`평균 절대 SHAP · ${shap.scale} · 대구 n=${shap.n}`}>
        <GlobalImportance shap={shap} />
        {top && <p className="shap-finding"><strong>{top.feature}</strong>의 평균 절대 기여도가 {fmt(top.mean_abs, 3)}으로 가장 큽니다. 이 순위는 대구 설명 대상 표본에 한정됩니다.</p>}
        <details className="method-details"><summary>평균 절대 SHAP 수치 확인</summary>
          <div className="table-wrap" tabIndex={0} role="region" aria-label="대구 XGBoost 평균 절대 SHAP 표"><table><thead><tr><th>변수</th><th>평균 |SHAP| · log(kWh/m³)</th></tr></thead><tbody>{shap.importance.map(entry => <tr key={entry.key}><td>{entry.feature}</td><td>{fmt(entry.mean_abs, 5)}</td></tr>)}</tbody></table></div>
        </details>
        <p className="chart-caption">입력 변수의 단위나 전력량이 아닌, 모델의 로그 예측에 미치는 기여도의 크기입니다. 전국 변수 중요도와 동일하지 않습니다.</p>
      </Panel>
      <Panel title="이 시설의 예측은 어떻게 만들어졌나" subtitle={`${data.meta.year}년 · XGBoost · 학습에 사용하지 않은 대구 시설`}>
        <div className="facility-stepper"><label><span>분석 시설</span><select value={row.facility_id} onChange={event => setFacilityId(event.target.value)}>{shap.predictions.map(entry => <option value={entry.facility_id} key={entry.facility_id}>{entry.name}</option>)}</select></label><div className="facility-stepper-buttons"><span aria-live="polite">{facilityIndex + 1} / {shap.n}</span><button className="icon-button" aria-label="이전 SHAP 분석 시설" disabled={facilityIndex === 0} onClick={() => setFacilityId(shap.predictions[facilityIndex - 1].facility_id)}><ChevronLeft size={17}/></button><button className="icon-button" aria-label="다음 SHAP 분석 시설" disabled={facilityIndex === shap.predictions.length - 1} onClick={() => setFacilityId(shap.predictions[facilityIndex + 1].facility_id)}><ChevronRight size={17}/></button></div></div>
        <div className="shap-prediction-summary" aria-live="polite"><div><span>관측 원단위</span><strong>{fmt(actual, 3)}<small>kWh/m³</small></strong></div><div><span>XGBoost 예측</span><strong>{fmt(row.predicted, 3)}<small>kWh/m³</small></strong></div></div>
        <div className="chart-legend"><span><i style={{ background: positive }} className="dot" />로그 예측을 높임 (+)</span><span><i style={{ background: negative }} className="dot" />로그 예측을 낮춤 (−)</span></div>
        <LocalContributions row={row} />
        <p className="chart-caption">기준값에 대한 변수별 기여 · log(kWh/m³). 막대의 색은 예측 방향이며 환경 성과의 좋고 나쁨을 뜻하지 않습니다.</p>
      </Panel>
    </div>
    <Panel title="기준값에서 예측까지, 계산 근거" subtitle={`${row.name} · ${data.meta.year}년 · XGBoost SHAP`} action={<DownloadLink file="MODEL_EVALUATION.md" label="SHAP 방법론·검증" />}>
      <div className="shap-equation" aria-label="로그 기준값과 SHAP 합을 지수 변환해 예측을 복원한 결과"><span>exp(<b>{fmt(row.base_value, 5)}</b><small>로그 기준값</small></span><span className="shap-operator">+</span><span><b>{signed(total)}</b><small>일곱 변수 SHAP 합</small></span><span className="shap-operator">) =</span><span><b>{fmt(row.reconstructed_predicted, 3)}</b><small>예측 kWh/m³</small></span></div>
      <p className="chart-caption">표시값은 반올림했습니다. SHAP 합은 log(kWh/m³)에서만 가산적입니다. 기여도 하나를 kWh/m³로 바꿔 서로 더할 수 없습니다. 기준값은 최적 운전 목표나 전국 평균 관측값이 아닙니다.</p>
      <details className="method-details"><summary>{row.name}의 입력값·기여도와 계산 검증</summary>
        <div className="table-wrap" tabIndex={0} role="region" aria-label={`${row.name}의 입력값과 SHAP 기여도 표`}><table><thead><tr><th>변수</th><th>모델 입력값</th><th>SHAP · log(kWh/m³)</th></tr></thead><tbody>{row.contributions.map(entry => <tr key={entry.key}><td>{entry.feature}</td><td>{entry.value === null ? '결측 → 학습자료 기준 대치' : typeof entry.value === 'number' ? fmt(entry.value, 4) : entry.value}</td><td>{signed(entry.shap_value)}</td></tr>)}</tbody></table></div>
        <p>기준 분포: 타 지역 학습자료 {shap.background_n}개. 공법 원핫 인코딩의 기여도를 원래 공법 변수로 합산합니다. 용량·유입량 입력은 자연로그 log(1+x)이며, SHAP의 목표 척도는 log(kWh/m³)입니다.</p>
        <p>로그 예측 가산성 검증의 최대 절대오차: {shap.max_additivity_error.toExponential(2)}. {shap.scope}</p>
        <p>{shap.note}</p>
      </details>
      <p className="chart-caption">출처: 한국환경공단 공공하수처리시설 현황 · {data.meta.year}년 하수도통계 대조 · analysis/model.py에서 재현.</p>
      <DownloadLink file="xgboost_shap.json" label="39개 시설 SHAP 계산 결과 JSON" />
    </Panel>
  </section>;
}
