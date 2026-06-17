from app.ml.salary_predictor import get_salary_model


def get_feature_importance(limit: int = 30) -> dict[str, object]:
    payload = get_salary_model()
    pipeline = payload["model"]
    feature_names = pipeline.named_steps["vectorizer"].get_feature_names_out()
    importances = pipeline.named_steps["model"].feature_importances_
    items = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)[:limit]
    total = sum(score for _, score in items) or 1
    return {
        "items": [{"feature": name, "score": round(float(score), 6), "percent": round(float(score / total * 100), 2)} for name, score in items],
        "method": "RandomForestRegressor.feature_importances_",
        "sample_count": payload["sample_count"],
    }
