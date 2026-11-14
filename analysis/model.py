from __future__ import annotations

import numpy as np
import pandas as pd
import shap
import xgboost
from xgboost import XGBRegressor
from sklearn.base import clone
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

FEATURES = ['log_capacity', 'log_inflow', 'bod_in', 'tn_in', 'tp_in', 'age_years', 'process_key']
LABELS = ['시설용량 (log)', '일평균 유입량 (log)', '유입 BOD', '유입 T-N', '유입 T-P', '가동기간', '처리공법']
XGB_PARAMS = dict(n_estimators=300, learning_rate=0.05, max_depth=4,
                  min_child_weight=5, subsample=0.8, colsample_bytree=0.9,
                  reg_alpha=0.1, reg_lambda=5.0, objective='reg:squarederror',
                  tree_method='hist', n_jobs=4, random_state=42)


def explain_xgboost(model, train, daegu):
    """Exact Tree SHAP on the fitted log-target model, never on observed outcomes.

    Background contains training facilities only. One-hot attributions are summed
    back to process_key before computing global mean absolute attribution. This
    preserves additivity but is not a grouped-coalition Shapley calculation.
    """
    if daegu.empty:
        return {'available': False, 'reason': '설명 가능한 대구 적격 시설 없음', 'model': 'XGBoost'}
    pipeline = model.regressor_
    prep, tree = pipeline.named_steps['prep'], pipeline.named_steps['model']
    background = train.sample(n=min(100, len(train)), random_state=42)
    transformed = prep.transform(daegu[FEATURES])
    background_matrix = prep.transform(background[FEATURES])
    explainer = shap.TreeExplainer(tree, data=background_matrix,
                                  feature_perturbation='interventional', model_output='raw')
    values = np.asarray(explainer.shap_values(transformed, check_additivity=True, approximate=False))
    base = float(explainer.expected_value)
    numeric_slice = prep.output_indices_['numeric']
    category_slice = prep.output_indices_['category']
    grouped = np.column_stack([values[:, numeric_slice], values[:, category_slice].sum(axis=1)])
    assert grouped.shape == (len(daegu), len(FEATURES))
    predicted_log = tree.predict(transformed).astype(float)
    reconstructed_log = base + grouped.sum(axis=1)
    # Float32 XGBoost margins can differ slightly from the double precision TreeSHAP sum.
    np.testing.assert_allclose(reconstructed_log, predicted_log, rtol=1e-5, atol=1e-5)
    predicted = model.predict(daegu[FEATURES]).astype(float)
    np.testing.assert_allclose(np.exp(reconstructed_log), predicted, rtol=2e-5, atol=1e-6)
    np.testing.assert_allclose(base, tree.predict(background_matrix).mean(), rtol=1e-5, atol=1e-5)
    local = []
    for i, (_, row) in enumerate(daegu.iterrows()):
        contributions = [{'key': key, 'feature': label, 'value': row[key],
                          'shap_value': float(grouped[i, j])}
                         for j, (key, label) in enumerate(zip(FEATURES, LABELS))]
        contributions.sort(key=lambda item: abs(item['shap_value']), reverse=True)
        for rank, contribution in enumerate(contributions, 1):
            contribution['rank'] = rank
        local.append({'facility_id': row.facility_id, 'name': row['name'],
                      'base_value': base, 'predicted_log': predicted_log[i], 'predicted': predicted[i],
                      'reconstructed_predicted': np.exp(reconstructed_log[i]),
                      'additivity_error': abs(reconstructed_log[i] - predicted_log[i]),
                      'contributions': contributions})
    importance = [{'key': key, 'feature': label, 'mean_abs': float(np.abs(grouped[:, j]).mean())}
                  for j, (key, label) in enumerate(zip(FEATURES, LABELS))]
    importance.sort(key=lambda item: item['mean_abs'], reverse=True)
    for rank, item in enumerate(importance, 1):
        item['rank'] = rank
    return {'available': True, 'model': 'XGBoost', 'scale': 'log(kWh/m³)',
            'method': 'TreeExplainer / interventional', 'feature_perturbation': 'interventional',
            'model_output': 'raw', 'approximate': False,
            'scope': '대구 독립 지역 평가 시설의 XGBoost 예측 설명', 'n': len(daegu),
            'background_n': len(background), 'background_facility_ids': background.facility_id.tolist(),
            'background_scope': '대구를 제외한 적격 훈련 시설에서 seed=42로 100개 무작위 추출',
            'base_value': base, 'baseline_prediction': np.exp(base),
            'features': [{'key': key, 'label': label} for key, label in zip(FEATURES, LABELS)],
            'importance': importance, 'predictions': local,
            'max_additivity_error': float(np.max(np.abs(reconstructed_log - predicted_log))),
            'versions': {'shap': shap.__version__, 'xgboost': xgboost.__version__},
            'note': '기여도는 자연로그 원단위 척도이며 exp(기준값 + 기여도 합)이 예측 kWh/m³이다. '
                    '양수는 기준 예측 대비 상승, 음수는 하락 방향이다. 원단위에 직접 더하지 않는다. '
                    '공법 원핫 기여도는 합산 후 중요도를 계산했다. 별도 그룹 Shapley 값은 아니다. '
                    '상관된 용량·유입량과 원핫 사이의 의존성을 깨는 interventional 배경 가정에 민감하며 인과효과·절감량이 아니다.'}


def metrics(y, pred):
    return {'mae': mean_absolute_error(y, pred), 'rmse': float(np.sqrt(mean_squared_error(y, pred))),
            'r2': r2_score(y, pred), 'n': len(y)}


def run_model(d: pd.DataFrame) -> dict:
    x = d.loc[d.benchmark_eligible].copy()
    x['log_capacity'] = np.log1p(x.capacity_m3_day)
    x['log_inflow'] = np.log1p(x.inflow_m3_day)
    train, daegu = x.loc[~x.is_daegu].copy(), x.loc[x.is_daegu].copy()
    if len(train) < 100 or train.match_key.nunique() < 50:
        return {'available': False, 'reason': '학습에 필요한 타 지역 시설 표본 부족', 'features': FEATURES}
    numeric = Pipeline([('impute', SimpleImputer(strategy='median', add_indicator=False)), ('scale', StandardScaler())])
    prep = ColumnTransformer([('numeric', numeric, FEATURES[:-1]),
        ('category', Pipeline([('impute', SimpleImputer(strategy='most_frequent')),
                             ('onehot', OneHotEncoder(handle_unknown='ignore', min_frequency=5, sparse_output=False))]), ['process_key'])])
    algorithms = {'Ridge 기준모델': Ridge(alpha=10),
                  'Random Forest': RandomForestRegressor(n_estimators=160, min_samples_leaf=5,
                                                         max_depth=18, n_jobs=-1, random_state=42),
                  'XGBoost': XGBRegressor(**XGB_PARAMS)}
    # No outcome-derived feature is permitted; annual energy, CO2, self-sufficiency and BOD energy intensity are absent.
    models = {name: TransformedTargetRegressor(regressor=Pipeline([('prep', clone(prep)), ('model', alg)]),
                                               func=np.log, inverse_func=np.exp) for name, alg in algorithms.items()}
    folds = list(GroupKFold(n_splits=5).split(train, groups=train.match_key))
    evaluations, predictions, fold_records, oof_records, preprocessing_audit = [], {}, [], [], []
    for name, model in models.items():
        oof = np.full(len(train), np.nan)
        fold_metrics = []
        for fold, (tr, va) in enumerate(folds):
            assert set(train.iloc[tr].match_key).isdisjoint(set(train.iloc[va].match_key))
            fitted = clone(model).fit(train.iloc[tr][FEATURES], train.iloc[tr].kwh_m3)
            p = fitted.predict(train.iloc[va][FEATURES]); oof[va] = p
            oof_records.extend({'model': name, 'facility_id': row.facility_id, 'group': row.match_key,
                                'fold': fold, 'actual': row.kwh_m3, 'predicted': pred}
                               for (_, row), pred in zip(train.iloc[va].iterrows(), p))
            fold_metrics.append(metrics(train.iloc[va].kwh_m3, p))
            if name == 'Random Forest':
                preprocessing_audit.append({'fold': fold, 'train_n': len(tr), 'validation_n': len(va),
                    'numeric_medians': dict(zip(FEATURES[:-1], fitted.regressor_.named_steps['prep']
                        .named_transformers_['numeric'].named_steps['impute'].statistics_))})
                fold_records.extend({'facility_id': fid, 'group': group, 'fold': fold} for fid, group in
                    zip(train.iloc[va].facility_id, train.iloc[va].match_key))
        evaluation = {'name': name, 'cv': metrics(train.kwh_m3, oof), 'folds': fold_metrics}
        models[name].fit(train[FEATURES], train.kwh_m3)
        p = models[name].predict(daegu[FEATURES]) if len(daegu) else np.array([])
        evaluation['daegu'] = metrics(daegu.kwh_m3, p) if len(daegu) > 1 else None
        evaluations.append(evaluation)
        predictions[name] = p
    # Model selection is made solely on non-Daegu CV MAE, before looking at regional errors.
    selected = min(evaluations, key=lambda m: m['cv']['mae'])['name']
    tr, va = folds[0]
    explainer = clone(models[selected]).fit(train.iloc[tr][FEATURES], train.iloc[tr].kwh_m3)
    importance = permutation_importance(explainer, train.iloc[va][FEATURES], train.iloc[va].kwh_m3,
                                        scoring='neg_mean_absolute_error', n_repeats=8, random_state=42, n_jobs=1)
    rows = []
    for i, (_, r) in enumerate(daegu.iterrows()):
        pred = predictions[selected][i]
        rows.append({'facility_id': r.facility_id, 'name': r['name'], 'actual': r.kwh_m3, 'predicted': pred,
                     'residual': r.kwh_m3 - pred, 'ratio': r.kwh_m3 / pred,
                     'rf_predicted': predictions['Random Forest'][i], 'baseline_predicted': predictions['Ridge 기준모델'][i],
                     'xgb_predicted': predictions['XGBoost'][i]})
    return {'available': True, 'target': 'kWh/m³ (유입량 기준)', 'selected': selected, 'train_n': len(train),
            'daegu_n': len(daegu), 'excluded_n': len(d)-len(x), 'seed': 42,
            'features': [{'key': k, 'label': label} for k, label in zip(FEATURES, LABELS)],
            'evaluations': evaluations, 'predictions': rows, 'fold_assignment': fold_records,
            'oof_predictions': oof_records, 'preprocessing_audit': preprocessing_audit,
            'xgb_parameters': XGB_PARAMS, 'shap': explain_xgboost(models['XGBoost'], train, daegu),
            'importance': sorted([{'feature': label, 'mean': mean, 'std': std} for label, mean, std in
                zip(LABELS, importance.importances_mean, importance.importances_std)], key=lambda a: a['mean'], reverse=True),
            'importance_n': len(va),
            'validation': '2025년 단면. 대구 전체를 학습에서 제외. 타 지역은 시설 그룹 단위 5-fold OOF 검증. 대구는 독립 지역 평가.',
            'limitation': '운영연도 종료 후 관측된 연평균 유입조건에 대한 설명·조건부 추정 모델. 미래 사전예측·최적 운전목표·절감 가능량이 아님. 미관측 운전·슬러지·고도처리 조건을 모두 통제하지 못함.'}
