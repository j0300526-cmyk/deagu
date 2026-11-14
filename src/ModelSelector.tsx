import { useId } from 'react';
import { Check, ArrowUpRight } from 'lucide-react';
import type { Model } from './types';
import { fmt } from './components';

export default function ModelSelector({ model, year, value, onChange }: {
  model: Model; year: number; value: string; onChange: (value: string) => void;
}) {
  const groupId = useId();
  return <fieldset className="model-selector">
    <legend>비교할 예측 모델</legend>
    <div className="model-selector-heading"><p>{year}년 · 같은 입력과 시설 그룹 분할로 비교</p><span>MAE 단위 kWh/m³ · 낮을수록 오차가 작음</span></div>
    <div className="model-options">{model.evaluations.map(evaluation => {
      const selected = evaluation.name === value;
      return <label className={`model-option ${selected ? 'is-selected' : ''}`} key={evaluation.name}>
        <input type="radio" name={groupId} value={evaluation.name} checked={selected} onChange={() => onChange(evaluation.name)} />
        <span className="model-option-top"><strong>{evaluation.name}</strong><span className="model-option-check" aria-hidden="true">{selected ? <Check size={15} /> : <ArrowUpRight size={15} />}</span></span>
        <span className="model-option-scores"><span><small>타 지역 교차검증</small><b>{fmt(evaluation.cv.mae, 3)}</b></span><span><small>대구 독립평가</small><b>{fmt(evaluation.daegu?.mae, 3)}</b></span></span>
        <span className="model-option-foot">{evaluation.name === model.selected ? '교차검증 MAE 기준 선택 모델' : '동일 조건 비교 모델'}<span>{selected ? '현재 표시 중' : '선택하기'}</span></span>
      </label>;
    })}</div>
  </fieldset>;
}
