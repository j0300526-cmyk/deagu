import { useState } from 'react';
import { FlaskConical, Layers3, ShieldCheck, Target, TrendingUp } from 'lucide-react';
import type { Analysis, Facility, Prediction } from './types';
import { DownloadLink, Empty, fmt, KPI, Note, Panel, Source } from './components';
import { ImportanceBars, PredictionScatter } from './charts';
import ShapInsights from './ShapInsights';
import ModelSelector from './ModelSelector';

export function modelPrediction(row: Prediction, algorithm: string): number {
  if (algorithm === 'XGBoost') return row.xgb_predicted;
  if (algorithm === 'Random Forest') return row.rf_predicted;
  return row.baseline_predicted;
}

export default function AIInsights({ data, onSelect }: { data: Analysis; onSelect: (facility: Facility) => void }) {
  const model = data.model;
  const [requestedAlgorithm, setAlgorithm] = useState('XGBoost');
  if (!model.available) return <Empty title="AI 모델 학습을 보류했습니다">{model.reason}</Empty>;
  const evaluation = model.evaluations.find(entry => entry.name === requestedAlgorithm)
    ?? model.evaluations.find(entry => entry.name === model.selected) ?? model.evaluations[0];
  const algorithm = evaluation.name;
  const score = evaluation.daegu;
  const rows = model.predictions.map(row => {
    const predicted = modelPrediction(row, algorithm);
    return { ...row, predicted, residual: row.actual - predicted, ratio: row.actual / predicted };
  });
  const anomalies = rows.toSorted((a, b) => Math.abs(b.residual) - Math.abs(a.residual)).slice(0, 6);

  return <>
    <div className="model-banner"><div className="model-badge"><FlaskConical size={23} /></div><div><span className="eyebrow">EXPLAINABLE MACHINE LEARNING</span><h2>예측의 차이는, 더 살펴볼 이유입니다.</h2><p>대구 전체를 학습에서 제외하고, 타 지역 {fmt(model.train_n, 0)}개 시설에서 학습했습니다.</p></div><span className="tag teal-tag">대구 독립 평가 {model.daegu_n}개</span></div>
    <Note tone="warning">AI 예측은 연평균 유입조건에 따른 추정입니다. 실측값·최적 전력사용량·달성 가능한 절감 목표가 아닙니다. 품질 기준에서 제외된 {model.excluded_n}개 전국 시설로 일반화하지 않습니다.</Note>
    <ModelSelector model={model} year={data.meta.year} value={algorithm} onChange={setAlgorithm} />
    <div className="kpi-grid">
      <KPI label="대구 평균 절대오차 · MAE" value={fmt(score?.mae, 3)} unit="kWh/m³" detail={`${algorithm} · 대구 독립평가 n=${score?.n ?? 0}`} icon={<Target size={18} />} />
      <KPI label="대구 평균 제곱근 오차 · RMSE" value={fmt(score?.rmse, 3)} unit="kWh/m³" detail="큰 오차에 더 큰 가중치를 두는 지표" icon={<TrendingUp size={18} />} />
      <KPI label="대구 결정계수 · R²" value={fmt(score?.r2, 3)} unit="" detail="음수는 평균 예측보다 오차가 크다는 의미" icon={<Layers3 size={18} />} />
      <KPI label="타 지역 교차검증 · MAE" value={fmt(evaluation.cv.mae, 3)} unit="kWh/m³" detail={`시설 그룹 5-fold OOF · n=${evaluation.cv.n}`} icon={<ShieldCheck size={18} />} />
    </div>
    <div className="grid-two">
      <Panel title="관측값과 AI 예측값" subtitle={`${data.meta.year}년 대구 독립평가 · ${algorithm} · 점선은 관측=예측`}><PredictionScatter rows={rows} /><p className="chart-caption">x: 관측 kWh/m³ · y: 예측 kWh/m³. 관측값은 원본 전력·유량에서 계산한 지표입니다. 잔차도 현재 선택한 모델 기준입니다.</p></Panel>
      <Panel title="변수를 섞으면 예측 오차는 어떻게 달라질까" subtitle={`${model.selected} · 타 지역 첫 검증 fold n=${model.importance_n}`}><ImportanceBars rows={model.importance} /><p className="chart-caption">Permutation Importance · 섞었을 때 MAE 증가 (kWh/m³), 8회. 이 차트는 성능 기준 선택 모델의 검증 결과입니다. 아래 XGBoost SHAP과 단위·표본·방법이 다릅니다.</p></Panel>
    </div>
    <Panel title="단순 기준모델과의 성능 비교" subtitle={`${data.meta.year}년 · 모델 선택은 타 지역 OOF MAE만 사용 · MAE·RMSE 단위 kWh/m³`} action={<DownloadLink file="MODEL_EVALUATION.md" label="모델 평가서" />}>
      <div className="table-wrap" tabIndex={0} role="region" aria-label="Ridge Random Forest XGBoost 성능 비교 표"><table><thead><tr><th>모델</th><th>타 지역 OOF MAE</th><th>타 지역 OOF RMSE</th><th>타 지역 OOF R²</th><th>대구 MAE</th><th>대구 RMSE</th><th>대구 R²</th></tr></thead><tbody>{model.evaluations.map(entry => <tr key={entry.name}><td><b>{entry.name}</b>{entry.name === model.selected && <small className="teal-text">OOF MAE 기준 선택</small>}</td><td>{fmt(entry.cv.mae, 3)}</td><td>{fmt(entry.cv.rmse, 3)}</td><td>{fmt(entry.cv.r2, 3)}</td><td>{fmt(entry.daegu?.mae, 3)}</td><td>{fmt(entry.daegu?.rmse, 3)}</td><td>{fmt(entry.daegu?.r2, 3)}</td></tr>)}</tbody></table></div>
    </Panel>
    <div className="section-tools"><span>세 모델의 시설별 교차검증 예측과 분할 근거</span><DownloadLink file="model_oof_predictions.csv" label="OOF 예측 CSV" /></div>
    <ShapInsights data={data} />
    <Panel title="관측·예측 차이가 큰 시설" subtitle={`${data.meta.year}년 · 표시 모델 ${algorithm} · 절대 잔차 상위 · 추가 확인 목록이며 비효율 판정이 아닙니다`} action={<DownloadLink file="daegu_predictions.csv" />}>
      <div className="table-wrap" tabIndex={0} role="region" aria-label="표시 모델의 관측 예측 잔차 표"><table><thead><tr><th>시설</th><th>관측 kWh/m³</th><th>예측 kWh/m³</th><th>잔차 kWh/m³</th><th>추가 검토</th></tr></thead><tbody>{anomalies.map(row => <tr key={row.facility_id}><td><button className="facility-name" onClick={() => { const facility = data.facilities.find(entry => entry.facility_id === row.facility_id); if (facility) onSelect(facility); }}>{row.name}</button></td><td>{fmt(row.actual, 3)}</td><td>{fmt(row.predicted, 3)}</td><td>{fmt(row.residual, 3)}</td><td className="muted">계측 범위·연계처리·수질 조건 확인</td></tr>)}</tbody></table></div>
    </Panel>
    <details className="method-details"><summary>입력 변수와 검증 설계</summary><p>{model.validation}</p><p>입력: {model.features.map(entry => entry.label).join(', ')}. 전력·탄소·자립율 등 목표 파생값 제외. 전처리는 각 훈련 fold 안에서 적합.</p><p>{model.limitation}</p></details>
    <Source data={data} />
  </>;
}
