from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction import DictVectorizer
from sklearn.neighbors import LocalOutlierFactor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM

from app.ml.data import MODEL_FEATURES, load_records

#数据清洗
def valid_records() -> list[dict[str, Any]]:
    return [r for r in load_records() if r["salary_mid"] > 0]

#特征构造函数
def rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    anomaly_features = MODEL_FEATURES + ["salary_mid", "salary_range"]
    result = []
    for r in records:
        row = {feature: r[feature] for feature in MODEL_FEATURES}
        row["salary_mid"] = r["salary_mid"]
        row["salary_range"] = max(r["salary_max"] - r["salary_min"], 0)
        result.append(row)
    return result

#统一封装特征预处理流程
def anomaly_pipeline(model: Any) -> Pipeline:
    return Pipeline([("vectorizer", DictVectorizer(sparse=False)), ("scaler", StandardScaler()), ("model", model)])

#异常原因描述
def describe_reason(record: dict[str, Any]) -> str:
    reasons = []
    if record["salary_mid"] > 80:
        reasons.append("薪资明显偏高")
    if record["salary_mid"] < 1:
        reasons.append("薪资明显偏低")
    if record["salary_max"] - record["salary_min"] > 60:
        reasons.append("薪资区间跨度过大")
    if record["text_length"] < 30:
        reasons.append("岗位描述过短")
    if record["skill_count"] == 0:
        reasons.append("缺少技能标签")
    return "、".join(reasons) or "综合特征与多数岗位差异较大"

#统一输出规范的异常结果结构
def format_anomaly(record: dict[str, Any], score: float, method: str) -> dict[str, Any]:
    return {
        "id": record["id"],
        "name": record["name"],
        "company": record["company"],
        "city": record["city"],
        "salary_text": record["salary_text"],
        "salary_mid": round(float(record["salary_mid"]), 2),
        "method": method,
        "score": round(float(score), 4),
        "reason": describe_reason(record),
    }

#简单统计异常检测
def detect_statistical(records: list[dict[str, Any]], method: str, limit: int) -> list[dict[str, Any]]:
    values = np.array([r["salary_mid"] for r in records], dtype=float)
    if method == "zscore":
        mean = values.mean()
        std = values.std() or 1
        scores = np.abs((values - mean) / std)
        indices = np.where(scores >= 2.5)[0]
        ranked = sorted(indices, key=lambda i: scores[i], reverse=True)[:limit]
        return [format_anomaly(records[i], scores[i], method) for i in ranked]
    q1, q3 = np.percentile(values, [25, 75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    indices = [i for i, value in enumerate(values) if value < lower or value > upper]
    ranked = sorted(indices, key=lambda i: abs(values[i] - np.median(values)), reverse=True)[:limit]
    return [format_anomaly(records[i], abs(values[i] - np.median(values)), method) for i in ranked]


def detect_anomalies(method: str = "isolation_forest", contamination: float = 0.05, limit: int = 50) -> dict[str, object]:
    records = valid_records()
    if len(records) < 20:
        return {"items": [], "method": method, "sample_count": len(records)}
    contamination = min(max(contamination, 0.01), 0.3)
    limit = min(max(limit, 1), 200)

    if method in {"zscore", "iqr"}:
        return {"items": detect_statistical(records, method, limit), "method": method, "sample_count": len(records)}

    x = rows(records)
    #lof 局部离群因子
    if method == "lof":
        model = anomaly_pipeline(LocalOutlierFactor(contamination=contamination))
        labels = model.fit_predict(x)
        scores = -model.named_steps["model"].negative_outlier_factor_
    #ocsvm 单类支持向量机
    elif method == "ocsvm":
        model = anomaly_pipeline(OneClassSVM(nu=contamination, gamma="scale"))
        labels = model.fit_predict(x)
        scores = -model.decision_function(x)

    #isolation_forest 孤立森林
    else:
        method = "isolation_forest"
        model = anomaly_pipeline(IsolationForest(contamination=contamination, random_state=42, n_jobs=-1))
        labels = model.fit_predict(x)
        scores = -model.decision_function(x)

    indices = [i for i, label in enumerate(labels) if label == -1]
    ranked = sorted(indices, key=lambda i: scores[i], reverse=True)[:limit]
    return {"items": [format_anomaly(records[i], scores[i], method) for i in ranked], "method": method, "sample_count": len(records)}
