import { useState } from 'react';
import { FlaskConical, ShieldCheck, Target } from 'lucide-react';
import type { Analysis, Facility, Prediction } from './types';
import { DownloadLink, Empty, fmt, KPI, Note, Panel, Source, Takeaway } from './components';
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
    <div className="kpi-grid model-kpis">
      <KPI label="대구 평균 절대오차 · MAE" value={fmt(score?.mae, 3)} unit="kWh/m³" detail={`${algorithm} · 대구 독립평가 n=${score?.n ?? 0}`} icon={<Target size={18} />} />
      <KPI label="타 지역 교차검증 · MAE" value={fmt(evaluation.cv.mae, 3)} unit="kWh/m³" detail={`시설 그룹 5-fold OOF · n=${evaluation.cv.n}`} icon={<ShieldCheck size={18} />} />
    </div>
    <div className="grid-two">
      <Panel title="관측값과 AI 예측값" subtitle={`${data.meta.year}년 대구 독립평가 · ${algorithm} · 점선은 관측=예측`}><PredictionScatter rows={rows} /><Takeaway source={`${data.meta.year}년 · 대구 독립평가 ${score?.n ?? 0}개 · kWh/m³`}>점이 대각선에서 멀수록 예측 오차가 큽니다. 현재 모델의 대구 평균 절대오차는 {fmt(score?.mae, 3)} kWh/m³이며 예측값은 절감 목표가 아닙니다.</Takeaway></Panel>
      <Panel title="예측에 중요한 입력은 무엇인가" subtitle={`${model.selected} · 타 지역 첫 검증 fold n=${model.importance_n}`}><ImportanceBars rows={model.importance} /><Takeaway source={`${data.meta.year}년 · Permutation Importance · MAE 증가 kWh/m³`}>{model.importance[0]?.feature ?? '상위 변수'}를 섞었을 때 예측 오차가 가장 크게 늘었습니다. 이는 모델의 예측 의존도이며 전력 사용의 원인이나 현장 개선 효과를 뜻하지 않습니다.</Takeaway></Panel>
    </div>
    <Panel title="단순 기준모델과의 성능 비교" subtitle={`${data.meta.year}년 · 모델 선택은 타 지역 OOF MAE만 사용 · MAE·RMSE 단위 kWh/m³`} action={<DownloadLink file="MODEL_EVALUATION.md" label="모델 평가서" />}>
      <Takeaway>타 지역 교차검증 오차가 가장 낮은 <b>{model.selected}</b>을 선택했습니다. 대구 열은 학습에 쓰지 않은 시설에서의 성능이며, 값이 작을수록 예측 오차가 작습니다.</Takeaway>
      <details className="data-details"><summary>세 모델의 MAE·RMSE·R² 전체 표 보기</summary><div className="table-wrap" tabIndex={0} role="region" aria-label="Ridge Random Forest XGBoost 성능 비교 표"><table><thead><tr><th>모델</th><th>타 지역 OOF MAE</th><th>타 지역 OOF RMSE</th><th>타 지역 OOF R²</th><th>대구 MAE</th><th>대구 RMSE</th><th>대구 R²</th></tr></thead><tbody>{model.evaluations.map(entry => <tr key={entry.name}><td><b>{entry.name}</b>{entry.name === model.selected && <small className="teal-text">OOF MAE 기준 선택</small>}</td><td>{fmt(entry.cv.mae, 3)}</td><td>{fmt(entry.cv.rmse, 3)}</td><td>{fmt(entry.cv.r2, 3)}</td><td>{fmt(entry.daegu?.mae, 3)}</td><td>{fmt(entry.daegu?.rmse, 3)}</td><td>{fmt(entry.daegu?.r2, 3)}</td></tr>)}</tbody></table></div></details>
    </Panel>
    <div className="section-tools"><span>세 모델의 시설별 교차검증 예측과 분할 근거</span><DownloadLink file="model_oof_predictions.csv" label="OOF 예측 CSV" /></div>
    <ShapInsights data={data} />
    <Panel title="관측·예측 차이가 큰 시설" subtitle={`${data.meta.year}년 · 표시 모델 ${algorithm} · 절대 잔차 상위 · 추가 확인 목록이며 비효율 판정이 아닙니다`} action={<DownloadLink file="daegu_predictions.csv" />}>
      <Takeaway>관측값과 예측값의 차이가 큰 곳은 계측 범위·연계처리·수질 조건을 추가 확인할 후보입니다. 차이가 크다는 사실만으로 운영 비효율을 뜻하지 않습니다.</Takeaway>
      <details className="data-details"><summary>잔차가 큰 시설 6곳의 수치 보기</summary><div className="table-wrap" tabIndex={0} role="region" aria-label="표시 모델의 관측 예측 잔차 표"><table><thead><tr><th>시설</th><th>관측 kWh/m³</th><th>예측 kWh/m³</th><th>잔차 kWh/m³</th><th>추가 검토</th></tr></thead><tbody>{anomalies.map(row => <tr key={row.facility_id}><td><button className="facility-name" onClick={() => { const facility = data.facilities.find(entry => entry.facility_id === row.facility_id); if (facility) onSelect(facility); }}>{row.name}</button></td><td>{fmt(row.actual, 3)}</td><td>{fmt(row.predicted, 3)}</td><td>{fmt(row.residual, 3)}</td><td className="muted">계측 범위·연계처리·수질 조건 확인</td></tr>)}</tbody></table></div></details>
    </Panel>
    <details className="method-details"><summary>입력 변수와 검증 설계</summary><p>{model.validation}</p><p>입력: {model.features.map(entry => entry.label).join(', ')}. 전력·탄소·자립율 등 목표 파생값 제외. 전처리는 각 훈련 fold 안에서 적합.</p><p>{model.limitation}</p></details>
    <Source data={data} />
  </>;
}
