from math import sqrt
from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.ml.cache import load_artifact, save_artifact
from app.ml.data import MODEL_FEATURES, salary_training_records, split_tags

ARTIFACT_NAME = "salary_predictor.joblib"


def build_row(features: dict[str, Any]) -> dict[str, Any]:
    tags = split_tags(features.get("tags", ""))
    row = {
        "city": features.get("city") or "未知",
        "education": features.get("education") or "不限",
        "recruit_type": features.get("recruit_type") or "社招",
        "company_scale": features.get("company_scale") or "未知",
        "financing_stage": features.get("financing_stage") or "未知",
        "industry": features.get("industry") or "未知",
        "category": features.get("category") or "其他",
        "salary_month": int(float(features.get("salary_month") or 12)),
        "text_length": int(float(features.get("text_length") or 500)),
        "skill_count": len(tags) if tags else int(float(features.get("skill_count") or 0)),
    }
    return row


def records_to_matrix(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], np.ndarray]:
    x = [{feature: r[feature] for feature in MODEL_FEATURES} for r in records]
    y = np.array([r["salary_mid"] for r in records], dtype=float)
    return x, y


def make_pipeline(model: Any) -> Pipeline:
    return Pipeline([("vectorizer", DictVectorizer(sparse=False)), ("model", model)])


def evaluate_model(model: Pipeline, x_test: list[dict[str, Any]], y_test: np.ndarray) -> dict[str, float]:
    pred = model.predict(x_test)
    return {
        "mae": round(float(mean_absolute_error(y_test, pred)), 2),
        "rmse": round(float(sqrt(mean_squared_error(y_test, pred))), 2),
        "r2": round(float(r2_score(y_test, pred)), 4),
    }


def train_salary_model() -> dict[str, Any]:
    records = salary_training_records()
    if len(records) < 20:
        raise ValueError("可用于训练薪资预测模型的数据不足")
    x, y = records_to_matrix(records)
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

    models = {
        "linear_regression": make_pipeline(LinearRegression()),
        "ridge": make_pipeline(Ridge(alpha=1.0)),
        "random_forest": make_pipeline(RandomForestRegressor(n_estimators=180, random_state=42, n_jobs=-1, min_samples_leaf=2)),
    }
    metrics = {}
    for name, model in models.items():
        model.fit(x_train, y_train)
        metrics[name] = evaluate_model(model, x_test, y_test)

    payload = {
        "model": models["random_forest"],
        "metrics": metrics,
        "sample_count": len(records),
        "target": "月薪中位数(K)",
    }
    save_artifact(ARTIFACT_NAME, payload)
    return payload


def get_salary_model() -> dict[str, Any]:
    cached = load_artifact(ARTIFACT_NAME)
    return cached if cached else train_salary_model()


def predict_salary(features: dict[str, Any]) -> dict[str, Any]:
    payload = get_salary_model()
    row = build_row(features)
    predicted = float(payload["model"].predict([row])[0])
    return {
        "predicted_salary": round(predicted, 2),
        "salary_unit": "K/月",
        "input_features": row,
        "metrics": payload["metrics"],
        "sample_count": payload["sample_count"],
    }


def salary_metrics() -> dict[str, Any]:
    payload = get_salary_model()
    return {"metrics": payload["metrics"], "sample_count": payload["sample_count"], "target": payload["target"]}
