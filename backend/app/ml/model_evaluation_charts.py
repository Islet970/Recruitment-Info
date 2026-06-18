from __future__ import annotations

import warnings
from math import sqrt
from pathlib import Path
from statistics import mean, median
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")

from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_validate, train_test_split
from sklearn.neighbors import LocalOutlierFactor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM

from app.ml.anomaly_detector import valid_records
from app.ml.association_rules import generate_association_rules
from app.ml.data import MODEL_FEATURES, salary_training_records
from app.ml.salary_predictor import make_pipeline, records_to_matrix

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "WenQuanYi Micro Hei", "Arial"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 150
plt.rcParams["savefig.dpi"] = 150
plt.rcParams["savefig.bbox"] = "tight"
plt.rcParams["savefig.pad_inches"] = 0.3

CHART_DIR = Path(__file__).resolve().parent / "evaluation_charts"
PALETTE = ["#2563eb", "#16a34a", "#f97316", "#9333ea", "#dc2626", "#0891b2", "#ca8a04"]


def save_fig(path: Path) -> None:
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    plt.tight_layout(pad=2.0)
    plt.savefig(path, format="png", facecolor="white", edgecolor="none")
    plt.close()


def evaluate_salary_models() -> dict[str, dict[str, float]]:
    records = salary_training_records()
    if len(records) < 20:
        raise ValueError("可用于训练薪资预测模型的数据不足")
    x, y = records_to_matrix(records)
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)
    models = {
        "LinearRegression": make_pipeline(LinearRegression()),
        "Ridge": make_pipeline(Ridge(alpha=1.0)),
        "RandomForest": make_pipeline(RandomForestRegressor(n_estimators=180, random_state=42, n_jobs=-1, min_samples_leaf=2)),
    }
    metrics = {}
    for name, model in models.items():
        model.fit(x_train, y_train)
        pred = model.predict(x_test)
        metrics[name] = {
            "MAE": float(mean_absolute_error(y_test, pred)),
            "RMSE": float(sqrt(mean_squared_error(y_test, pred))),
            "R²": float(r2_score(y_test, pred)),
        }
    return metrics


def cross_validate_salary_models() -> dict[str, dict[str, float]]:
    records = salary_training_records()
    x, y = records_to_matrix(records)
    models = {
        "LinearRegression": make_pipeline(LinearRegression()),
        "Ridge": make_pipeline(Ridge(alpha=1.0)),
        "RandomForest": make_pipeline(RandomForestRegressor(n_estimators=180, random_state=42, n_jobs=-1, min_samples_leaf=2)),
    }
    scoring = {"MAE": "neg_mean_absolute_error", "RMSE": "neg_root_mean_squared_error", "R²": "r2"}
    folds = min(5, max(2, len(records) // 20))
    cv = KFold(n_splits=folds, shuffle=True, random_state=42)
    result = {}
    for name, model in models.items():
        scores = cross_validate(model, x, y, cv=cv, scoring=scoring, n_jobs=None)
        result[name] = {
            "MAE": float(-scores["test_MAE"].mean()),
            "RMSE": float(-scores["test_RMSE"].mean()),
            "R²": float(scores["test_R²"].mean()),
        }
    return result


def anomaly_feature_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for record in records:
        row = {feature: record[feature] for feature in MODEL_FEATURES}
        row["salary_mid"] = record["salary_mid"]
        row["salary_range"] = max(record["salary_max"] - record["salary_min"], 0)
        rows.append(row)
    return rows


def evaluate_anomaly_methods(contamination: float = 0.05) -> dict[str, dict[str, float]]:
    records = valid_records()
    if len(records) < 20:
        raise ValueError("可用于异常检测的数据不足")
    contamination = min(max(contamination, 0.01), 0.3)
    values = np.array([record["salary_mid"] for record in records], dtype=float)
    matrix = anomaly_feature_rows(records)
    vectorizer = DictVectorizer(sparse=False)
    scaled = StandardScaler().fit_transform(vectorizer.fit_transform(matrix))
    methods: dict[str, tuple[np.ndarray, np.ndarray]] = {}

    zscores = np.abs((values - values.mean()) / (values.std() or 1))
    methods["ZScore"] = (np.where(zscores >= 2.5, -1, 1), zscores)

    q1, q3 = np.percentile(values, [25, 75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    iqr_scores = np.abs(values - np.median(values))
    methods["IQR"] = (np.where((values < lower) | (values > upper), -1, 1), iqr_scores)

    isolation = IsolationForest(contamination=contamination, random_state=42, n_jobs=-1)
    isolation_labels = isolation.fit_predict(scaled)
    methods["IsolationForest"] = (isolation_labels, -isolation.decision_function(scaled))

    lof = LocalOutlierFactor(contamination=contamination)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Duplicate values are leading to incorrect results.*")
        lof_labels = lof.fit_predict(scaled)
    methods["LOF"] = (lof_labels, -lof.negative_outlier_factor_)

    ocsvm = OneClassSVM(nu=contamination, gamma="scale")
    ocsvm_labels = ocsvm.fit_predict(scaled)
    methods["OneClassSVM"] = (ocsvm_labels, -ocsvm.decision_function(scaled))

    anomaly_sets = {name: set(np.where(labels == -1)[0].tolist()) for name, (labels, _) in methods.items()}
    metrics = {}
    for name, (labels, scores) in methods.items():
        anomaly_count = int(np.sum(labels == -1))
        peers = [other for other in anomaly_sets if other != name]
        overlaps = []
        for peer in peers:
            union = anomaly_sets[name] | anomaly_sets[peer]
            overlaps.append(len(anomaly_sets[name] & anomaly_sets[peer]) / len(union) if union else 1.0)
        metrics[name] = {
            "异常数": float(anomaly_count),
            "异常率%": float(anomaly_count / len(records) * 100),
            "平均分": float(mean(scores)),
            "中位分": float(median(scores)),
            "最高分": float(max(scores)),
            "共识重合": float(mean(overlaps) if overlaps else 0),
        }
    return metrics


# ══════════════════════════════════════════════
#  Chart 1: Salary — Error Metrics (MAE + RMSE)
# ══════════════════════════════════════════════
def chart_salary_error_comparison(metrics: dict[str, dict[str, float]]) -> Path:
    models = list(metrics)
    mae_vals = [metrics[m]["MAE"] for m in models]
    rmse_vals = [metrics[m]["RMSE"] for m in models]

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(models))
    w = 0.32

    bars1 = ax.bar(x - w / 2, mae_vals, w, color=PALETTE[0], edgecolor="white", linewidth=0.6, label="MAE")
    bars2 = ax.bar(x + w / 2, rmse_vals, w, color=PALETTE[1], edgecolor="white", linewidth=0.6, label="RMSE")

    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.12,
                f"{bar.get_height():.2f}", ha="center", va="bottom", fontsize=10, fontweight="bold")
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.12,
                f"{bar.get_height():.2f}", ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=12)
    ax.set_ylabel("误差值（K/月）", fontsize=12)
    ax.set_title("薪资预测模型 · 误差指标对比", fontsize=16, fontweight="bold", pad=16)
    ax.legend(fontsize=11, loc="upper left")
    ax.set_ylim(0, max(mae_vals + rmse_vals) * 1.25)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    path = CHART_DIR / "01_salary_error_comparison.png"
    save_fig(path)
    return path


# ══════════════════════════════════════════════
#  Chart 2: Salary — R² Comparison
# ══════════════════════════════════════════════
def chart_salary_r2_comparison(metrics: dict[str, dict[str, float]]) -> Path:
    models = list(metrics)
    r2_vals = [metrics[m]["R²"] for m in models]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    colors = [PALETTE[i % len(PALETTE)] for i in range(len(models))]
    bars = ax.barh(models, r2_vals, color=colors, edgecolor="white", linewidth=0.8, height=0.45)

    for bar, val in zip(bars, r2_vals):
        ax.text(bar.get_width() + 0.008, bar.get_y() + bar.get_height() / 2,
                f"{val:.4f}", va="center", fontsize=12, fontweight="bold")

    ax.set_xlabel("R² 决定系数", fontsize=12)
    ax.set_title("薪资预测模型 · R² 决定系数对比", fontsize=16, fontweight="bold", pad=16)
    ax.set_xlim(0, max(r2_vals) * 1.18)
    ax.grid(axis="x", alpha=0.3, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.invert_yaxis()

    path = CHART_DIR / "02_salary_r2_comparison.png"
    save_fig(path)
    return path


# ══════════════════════════════════════════════
#  Chart 3: Salary — Cross-Validation Radar
# ══════════════════════════════════════════════
def chart_salary_cv_radar(cv_metrics: dict[str, dict[str, float]]) -> Path:
    models = list(cv_metrics)
    metric_names = ["MAE", "RMSE", "R²"]
    n_metrics = len(metric_names)

    # Normalize each metric to [0,1] for radar; for error metrics lower is better → invert
    raw = {m: [cv_metrics[m][k] for k in metric_names] for m in models}
    all_vals = {k: [cv_metrics[m][k] for m in models] for k in metric_names}

    normalized = {}
    for m in models:
        norm = []
        for k in metric_names:
            vals = all_vals[k]
            lo, hi = min(vals), max(vals)
            if hi == lo:
                norm.append(0.5)
            elif k == "R²":
                norm.append((cv_metrics[m][k] - lo) / (hi - lo))
            else:
                norm.append(1.0 - (cv_metrics[m][k] - lo) / (hi - lo))
        normalized[m] = norm

    angles = np.linspace(0, 2 * np.pi, n_metrics, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"projection": "polar"})
    for i, m in enumerate(models):
        values = normalized[m] + normalized[m][:1]
        ax.fill(angles, values, alpha=0.12, color=PALETTE[i])
        ax.plot(angles, values, "o-", linewidth=2.2, color=PALETTE[i], label=m, markersize=6)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metric_names, fontsize=12, fontweight="bold")
    ax.set_yticklabels([])
    ax.set_title("薪资预测模型 · 交叉验证综合对比（雷达图）", fontsize=15, fontweight="bold", pad=28)
    ax.legend(loc="upper right", bbox_to_anchor=(1.32, 1.12), fontsize=11)
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.4, linestyle="--")

    path = CHART_DIR / "03_salary_cv_radar.png"
    save_fig(path)
    return path


# ══════════════════════════════════════════════
#  Chart 4: Anomaly — Volume (Anomaly Count + Rate)
# ══════════════════════════════════════════════
def chart_anomaly_volume(metrics: dict[str, dict[str, float]]) -> Path:
    methods = list(metrics)
    counts = [metrics[m]["异常数"] for m in methods]
    rates = [metrics[m]["异常率%"] for m in methods]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

    colors1 = [PALETTE[i % len(PALETTE)] for i in range(len(methods))]
    bars1 = ax1.bar(methods, counts, color=colors1, edgecolor="white", linewidth=0.7)
    for bar, val in zip(bars1, counts):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                 str(int(val)), ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax1.set_title("异常岗位数量", fontsize=14, fontweight="bold")
    ax1.set_ylabel("异常数", fontsize=11)
    ax1.tick_params(axis="x", rotation=20)
    ax1.grid(axis="y", alpha=0.3, linestyle="--")
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    bars2 = ax2.bar(methods, rates, color=colors1, edgecolor="white", linewidth=0.7)
    for bar, val in zip(bars2, rates):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.08,
                 f"{val:.2f}%", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax2.set_title("异常率 (%)", fontsize=14, fontweight="bold")
    ax2.set_ylabel("异常率 %", fontsize=11)
    ax2.tick_params(axis="x", rotation=20)
    ax2.grid(axis="y", alpha=0.3, linestyle="--")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    fig.suptitle("异常检测算法 · 识别规模对比", fontsize=16, fontweight="bold", y=1.02)

    path = CHART_DIR / "04_anomaly_volume.png"
    save_fig(path)
    return path


# ══════════════════════════════════════════════
#  Chart 5: Anomaly — Score Distribution (Grouped Bar)
# ══════════════════════════════════════════════
def chart_anomaly_scores(metrics: dict[str, dict[str, float]]) -> Path:
    methods = list(metrics)
    score_types = ["平均分", "中位分", "最高分"]

    fig, ax = plt.subplots(figsize=(11, 6))
    x = np.arange(len(methods))
    w = 0.22

    for i, st in enumerate(score_types):
        vals = [metrics[m][st] for m in methods]
        bars = ax.bar(x + (i - 1) * w, vals, w, color=PALETTE[i], edgecolor="white", linewidth=0.5, label=st)
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.06,
                    f"{bar.get_height():.2f}", ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(methods, fontsize=11)
    ax.set_ylabel("异常得分", fontsize=12)
    ax.set_title("异常检测算法 · 得分分布对比", fontsize=16, fontweight="bold", pad=16)
    ax.legend(fontsize=11, loc="upper left")
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    all_vals = [metrics[m][st] for m in methods for st in score_types]
    ax.set_ylim(0, max(all_vals) * 1.22)

    path = CHART_DIR / "05_anomaly_scores.png"
    save_fig(path)
    return path


# ══════════════════════════════════════════════
#  Chart 6: Anomaly — Consensus Overlap
# ══════════════════════════════════════════════
def chart_anomaly_consensus(metrics: dict[str, dict[str, float]]) -> Path:
    methods = list(metrics)
    overlaps = [metrics[m]["共识重合"] for m in methods]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    colors = [PALETTE[i % len(PALETTE)] for i in range(len(methods))]
    bars = ax.barh(methods, overlaps, color=colors, edgecolor="white", linewidth=0.8, height=0.45)

    for bar, val in zip(bars, overlaps):
        ax.text(bar.get_width() + 0.006, bar.get_y() + bar.get_height() / 2,
                f"{val:.4f}", va="center", fontsize=12, fontweight="bold")

    ax.set_xlabel("Jaccard 共识重合度", fontsize=12)
    ax.set_title("异常检测算法 · 共识重合度对比", fontsize=16, fontweight="bold", pad=16)
    ax.set_xlim(0, max(overlaps) * 1.18)
    ax.grid(axis="x", alpha=0.3, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.invert_yaxis()

    path = CHART_DIR / "06_anomaly_consensus.png"
    save_fig(path)
    return path


# ══════════════════════════════════════════════
#  Chart 7: Salary — Holdout vs CV Side-by-Side
# ══════════════════════════════════════════════
def chart_salary_holdout_vs_cv(holdout: dict[str, dict[str, float]],
                               cv: dict[str, dict[str, float]]) -> Path:
    models = list(holdout)
    metrics_map = ["MAE", "RMSE", "R²"]

    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))

    for ax_idx, metric in enumerate(metrics_map):
        ax = axes[ax_idx]
        x = np.arange(len(models))
        w = 0.32

        ho_vals = [holdout[m][metric] for m in models]
        cv_vals = [cv[m][metric] for m in models]

        bars1 = ax.bar(x - w / 2, ho_vals, w, color=PALETTE[0], edgecolor="white", linewidth=0.5, label="留出测试集")
        bars2 = ax.bar(x + w / 2, cv_vals, w, color=PALETTE[2], edgecolor="white", linewidth=0.5, label="K折交叉验证")

        for bar in bars1:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                    f"{bar.get_height():.2f}", ha="center", va="bottom", fontsize=8, fontweight="bold")
        for bar in bars2:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                    f"{bar.get_height():.2f}", ha="center", va="bottom", fontsize=8, fontweight="bold")

        ax.set_xticks(x)
        ax.set_xticklabels(models, fontsize=9)
        ax.set_title(metric, fontsize=14, fontweight="bold")
        ax.grid(axis="y", alpha=0.3, linestyle="--")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        all_vals = ho_vals + cv_vals
        ax.set_ylim(0, max(all_vals) * 1.28)

        if ax_idx == 0:
            ax.legend(fontsize=10, loc="upper left")

    fig.suptitle("薪资预测模型 · 留出测试 vs 交叉验证 逐指标对比", fontsize=16, fontweight="bold", y=1.03)

    path = CHART_DIR / "07_salary_holdout_vs_cv.png"
    save_fig(path)
    return path


# ══════════════════════════════════════════════
#  Association Rules — Parameter Grid Evaluation
# ══════════════════════════════════════════════
def evaluate_association_param_grid() -> dict[str, Any]:
    supports = [0.005, 0.01, 0.02, 0.05, 0.10]
    confidences = [0.2, 0.3, 0.4, 0.6, 0.8]
    grid: dict[str, list[dict[str, float]]] = {}
    for sup in supports:
        for conf in confidences:
            result = generate_association_rules(min_support=sup, min_confidence=conf, limit=200)
            rules = result["rules"]
            total = result["transaction_count"]
            if not rules:
                grid[f"{sup},{conf}"] = []
                continue
            supports_vals = [r["support"] for r in rules]
            confidences_vals = [r["confidence"] for r in rules]
            lifts = [r["lift"] for r in rules]
            grid[f"{sup},{conf}"] = [{
                "rule_count": len(rules),
                "avg_support": mean(supports_vals),
                "max_support": max(supports_vals),
                "avg_confidence": mean(confidences_vals),
                "max_confidence": max(confidences_vals),
                "avg_lift": mean(lifts),
                "max_lift": max(lifts),
            }]
    return {"grid": grid, "supports": supports, "confidences": confidences}


# ══════════════════════════════════════════════
#  Chart 8: Association — Rule Count Heatmap
# ══════════════════════════════════════════════
def chart_association_param_heatmap(eval_data: dict[str, Any]) -> Path:
    supports = eval_data["supports"]
    confidences = eval_data["confidences"]
    grid = eval_data["grid"]
    matrix = np.zeros((len(confidences), len(supports)))
    for j, sup in enumerate(supports):
        for i, conf in enumerate(confidences):
            entry = grid.get(f"{sup},{conf}", [])
            matrix[i, j] = entry[0]["rule_count"] if entry else 0

    fig, ax = plt.subplots(figsize=(10, 7))
    im = ax.imshow(matrix, cmap="YlOrRd", aspect="auto", vmin=0)

    for i in range(len(confidences)):
        for j in range(len(supports)):
            val = int(matrix[i, j])
            ax.text(j, i, str(val), ha="center", va="center",
                    fontsize=11, fontweight="bold",
                    color="white" if matrix[i, j] > matrix.max() * 0.55 else "black")

    ax.set_xticks(range(len(supports)))
    ax.set_xticklabels([str(s) for s in supports], fontsize=11)
    ax.set_yticks(range(len(confidences)))
    ax.set_yticklabels([str(c) for c in confidences], fontsize=11)
    ax.set_xlabel("min_support", fontsize=13)
    ax.set_ylabel("min_confidence", fontsize=13)
    ax.set_title("关联规则 · 参数网格搜索（规则数量热力图）", fontsize=16, fontweight="bold", pad=16)
    fig.colorbar(im, ax=ax, shrink=0.82, label="规则数量")

    path = CHART_DIR / "08_association_param_heatmap.png"
    save_fig(path)
    return path


# ══════════════════════════════════════════════
#  Chart 9: Association — Lift Quality by Confidence
# ══════════════════════════════════════════════
def chart_association_quality_bars(eval_data: dict[str, Any]) -> Path:
    confidences = eval_data["confidences"]
    grid = eval_data["grid"]
    avg_lifts = []
    max_lifts = []
    for conf in confidences:
        entry = grid.get(f"0.02,{conf}", [])
        avg_lifts.append(entry[0]["avg_lift"] if entry else 0)
        max_lifts.append(entry[0]["max_lift"] if entry else 0)

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(confidences))
    w = 0.32
    bars1 = ax.bar(x - w / 2, avg_lifts, w, color=PALETTE[0], edgecolor="white", linewidth=0.6, label="平均 Lift")
    bars2 = ax.bar(x + w / 2, max_lifts, w, color=PALETTE[2], edgecolor="white", linewidth=0.6, label="最高 Lift")
    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.08,
                f"{bar.get_height():.2f}", ha="center", va="bottom", fontsize=10, fontweight="bold")
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.08,
                f"{bar.get_height():.2f}", ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels([f"conf={c}" for c in confidences], fontsize=11)
    ax.set_ylabel("Lift 值", fontsize=12)
    ax.set_title("关联规则 · 不同置信度下 Lift 质量对比 (min_support=0.02)", fontsize=15, fontweight="bold", pad=16)
    ax.legend(fontsize=11, loc="upper left")
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    all_vals = avg_lifts + max_lifts
    ax.set_ylim(0, max(all_vals) * 1.25)

    path = CHART_DIR / "09_association_quality_bars.png"
    save_fig(path)
    return path


# ══════════════════════════════════════════════
#  Chart 10: Association — Support vs Confidence Scatter
# ══════════════════════════════════════════════
def chart_association_support_confidence_scatter() -> Path:
    result = generate_association_rules(min_support=0.01, min_confidence=0.3, limit=200)
    rules = result["rules"]
    if not rules:
        fig, ax = plt.subplots(figsize=(9, 7))
        ax.text(0.5, 0.5, "无规则数据", ha="center", va="center", fontsize=16, transform=ax.transAxes)
        path = CHART_DIR / "10_association_support_confidence_scatter.png"
        save_fig(path)
        return path

    supports = [r["support"] for r in rules]
    confidences = [r["confidence"] for r in rules]
    lifts = [r["lift"] for r in rules]

    fig, ax = plt.subplots(figsize=(10, 7))
    sc = ax.scatter(supports, confidences, c=lifts, cmap="plasma", s=60, alpha=0.75, edgecolors="white", linewidth=0.4)
    cbar = fig.colorbar(sc, ax=ax, shrink=0.82)
    cbar.set_label("Lift", fontsize=12)

    for i in range(min(8, len(rules))):
        ax.annotate(f"{rules[i]['antecedent'][0]}→{rules[i]['consequent'][0]}",
                    (supports[i], confidences[i]),
                    fontsize=7, alpha=0.7, xytext=(5, 5), textcoords="offset points")

    ax.set_xlabel("Support", fontsize=13)
    ax.set_ylabel("Confidence", fontsize=13)
    ax.set_title("关联规则 · Support-Confidence 散点图 (颜色=Lift)", fontsize=16, fontweight="bold", pad=16)
    ax.grid(alpha=0.25, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    path = CHART_DIR / "10_association_support_confidence_scatter.png"
    save_fig(path)
    return path


# ══════════════════════════════════════════════
#  Chart 11: Association — Rule Count by Support
# ══════════════════════════════════════════════
def chart_association_rule_count_lines(eval_data: dict[str, Any]) -> Path:
    supports = eval_data["supports"]
    confidences = eval_data["confidences"]
    grid = eval_data["grid"]

    fig, ax = plt.subplots(figsize=(10, 6.5))
    for i, conf in enumerate(confidences):
        counts = []
        for sup in supports:
            entry = grid.get(f"{sup},{conf}", [])
            counts.append(entry[0]["rule_count"] if entry else 0)
        ax.plot(supports, counts, "o-", linewidth=2.2, markersize=7,
                color=PALETTE[i % len(PALETTE)], label=f"confidence={conf}")

    ax.set_xlabel("min_support", fontsize=13)
    ax.set_ylabel("规则数量", fontsize=13)
    ax.set_title("关联规则 · 不同置信度下规则数量随 Support 变化", fontsize=15, fontweight="bold", pad=16)
    ax.legend(fontsize=10, loc="upper right")
    ax.grid(alpha=0.3, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xscale("log")

    path = CHART_DIR / "11_association_rule_count_comparison.png"
    save_fig(path)
    return path


# ══════════════════════════════════════════════
#  Feature Importance — Cross-Model Extraction
# ══════════════════════════════════════════════
def extract_all_model_importances() -> dict[str, Any]:
    records = salary_training_records()
    if len(records) < 20:
        raise ValueError("可用于训练的数据不足")
    x, y = records_to_matrix(records)
    x_train, _, y_train, _ = train_test_split(x, y, test_size=0.2, random_state=42)

    models = {
        "LinearRegression": make_pipeline(LinearRegression()),
        "Ridge": make_pipeline(Ridge(alpha=1.0)),
        "RandomForest": make_pipeline(RandomForestRegressor(n_estimators=180, random_state=42, n_jobs=-1, min_samples_leaf=2)),
    }

    all_importances: dict[str, dict[str, float]] = {}
    feature_names: list[str] = []

    for name, model in models.items():
        model.fit(x_train, y_train)
        if feature_names:
            assert list(model.named_steps["vectorizer"].get_feature_names_out()) == feature_names, "特征名不一致"
        else:
            feature_names = list(model.named_steps["vectorizer"].get_feature_names_out())

        if name == "RandomForest":
            raw = model.named_steps["model"].feature_importances_
        else:
            raw = np.abs(model.named_steps["model"].coef_)
        total = raw.sum() or 1
        all_importances[name] = {fn: float(raw[i] / total) for i, fn in enumerate(feature_names)}

    return {"importances": all_importances, "feature_names": feature_names}


# ══════════════════════════════════════════════
#  Chart 12: Feature Importance — Top-20 Grouped Bar
# ══════════════════════════════════════════════
def chart_feature_importance_top20(fi_data: dict[str, Any]) -> Path:
    importances = fi_data["importances"]
    feature_names = fi_data["feature_names"]
    model_names = ["LinearRegression", "Ridge", "RandomForest"]

    rf_imp = importances["RandomForest"]
    top_indices = sorted(range(len(feature_names)), key=lambda i: rf_imp[feature_names[i]], reverse=True)[:20]
    top_features = [feature_names[i] for i in top_indices]
    short_names = [fn.split("=")[-1] if "=" in fn else fn for fn in top_features]

    fig, ax = plt.subplots(figsize=(14, 7))
    x = np.arange(len(top_features))
    w = 0.25

    for mi, mname in enumerate(model_names):
        vals = [importances[mname][fn] * 100 for fn in top_features]
        bars = ax.bar(x + (mi - 1) * w, vals, w, color=PALETTE[mi], edgecolor="white", linewidth=0.4, label=mname)
        for bar in bars:
            h = bar.get_height()
            if h > 0.3:
                ax.text(bar.get_x() + bar.get_width() / 2, h + 0.08,
                        f"{h:.1f}", ha="center", va="bottom", fontsize=6.5, fontweight="bold", rotation=90)

    ax.set_xticks(x)
    ax.set_xticklabels(short_names, fontsize=8, rotation=45, ha="right")
    ax.set_ylabel("重要性 (%)", fontsize=12)
    ax.set_title("特征重要性 · Top-20 三模型对比", fontsize=16, fontweight="bold", pad=16)
    ax.legend(fontsize=11, loc="upper right")
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    path = CHART_DIR / "12_feature_importance_top20.png"
    save_fig(path)
    return path


# ══════════════════════════════════════════════
#  Chart 13: Feature Importance — Pairwise Correlation Scatter
# ══════════════════════════════════════════════
def chart_feature_importance_correlation(fi_data: dict[str, Any]) -> Path:
    importances = fi_data["importances"]
    feature_names = fi_data["feature_names"]
    pairs = [("LinearRegression", "Ridge"), ("LinearRegression", "RandomForest"), ("Ridge", "RandomForest")]

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    for ax_idx, (ma, mb) in enumerate(pairs):
        ax = axes[ax_idx]
        vals_a = [importances[ma][fn] * 100 for fn in feature_names]
        vals_b = [importances[mb][fn] * 100 for fn in feature_names]
        ax.scatter(vals_a, vals_b, alpha=0.5, s=25, color=PALETTE[ax_idx], edgecolors="white", linewidth=0.3)

        corr = float(np.corrcoef(vals_a, vals_b)[0, 1])
        ax.set_xlabel(f"{ma} 重要性 (%)", fontsize=10)
        ax.set_ylabel(f"{mb} 重要性 (%)", fontsize=10)
        ax.set_title(f"{ma} vs {mb}\nr = {corr:.3f}", fontsize=12, fontweight="bold")
        ax.grid(alpha=0.25, linestyle="--")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        lim = max(max(vals_a), max(vals_b)) * 1.12
        ax.set_xlim(0, lim)
        ax.set_ylim(0, lim)
        ax.plot([0, lim], [0, lim], "k--", alpha=0.2, linewidth=0.8)

    fig.suptitle("特征重要性 · 三模型两两相关性", fontsize=16, fontweight="bold", y=1.02)

    path = CHART_DIR / "13_feature_importance_correlation.png"
    save_fig(path)
    return path


# ══════════════════════════════════════════════
#  Chart 14: Feature Importance — Top-N Overlap
# ══════════════════════════════════════════════
def chart_feature_importance_overlap(fi_data: dict[str, Any]) -> Path:
    importances = fi_data["importances"]
    feature_names = fi_data["feature_names"]
    model_names = ["LinearRegression", "Ridge", "RandomForest"]
    top_ns = [10, 20, 30]

    model_top_sets: dict[str, dict[int, set[str]]] = {}
    for mname in model_names:
        imp = importances[mname]
        ranked = sorted(feature_names, key=lambda fn: imp[fn], reverse=True)
        model_top_sets[mname] = {n: set(ranked[:n]) for n in top_ns}

    fig, ax = plt.subplots(figsize=(11, 6))
    x = np.arange(len(top_ns))
    w = 0.22
    pairs_labels = [("LR∩Ridge", "LinearRegression", "Ridge", PALETTE[0]),
                    ("LR∩RF", "LinearRegression", "RandomForest", PALETTE[1]),
                    ("Ridge∩RF", "Ridge", "RandomForest", PALETTE[2]),
                    ("三者∩", None, None, PALETTE[3])]

    for pi, (label, ma, mb, color) in enumerate(pairs_labels):
        vals = []
        for n in top_ns:
            if ma is None:
                overlap = model_top_sets["LinearRegression"][n] & model_top_sets["Ridge"][n] & model_top_sets["RandomForest"][n]
            else:
                overlap = model_top_sets[ma][n] & model_top_sets[mb][n]
            vals.append(len(overlap))
        bars = ax.bar(x + (pi - 1.5) * w, vals, w, color=color, edgecolor="white", linewidth=0.5, label=label)
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.25,
                    str(int(bar.get_height())), ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels([f"Top-{n}" for n in top_ns], fontsize=12)
    ax.set_ylabel("重叠特征数", fontsize=12)
    ax.set_title("特征重要性 · 三模型 Top-N 特征重叠对比", fontsize=16, fontweight="bold", pad=16)
    ax.legend(fontsize=10, loc="upper left")
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    path = CHART_DIR / "14_feature_importance_overlap.png"
    save_fig(path)
    return path


def generate_charts() -> list[Path]:
    salary_holdout = evaluate_salary_models()
    salary_cv = cross_validate_salary_models()
    anomaly_metrics = evaluate_anomaly_methods()
    created = []

    p = chart_salary_error_comparison(salary_holdout)
    created.append(p)
    print(p)

    p = chart_salary_r2_comparison(salary_holdout)
    created.append(p)
    print(p)

    p = chart_salary_cv_radar(salary_cv)
    created.append(p)
    print(p)

    p = chart_anomaly_volume(anomaly_metrics)
    created.append(p)
    print(p)

    p = chart_anomaly_scores(anomaly_metrics)
    created.append(p)
    print(p)

    p = chart_anomaly_consensus(anomaly_metrics)
    created.append(p)
    print(p)

    p = chart_salary_holdout_vs_cv(salary_holdout, salary_cv)
    created.append(p)
    print(p)

    print("评测关联规则参数网格 ...")
    assoc_grid = evaluate_association_param_grid()

    for fn in (
        lambda: chart_association_param_heatmap(assoc_grid),
        lambda: chart_association_quality_bars(assoc_grid),
        lambda: chart_association_support_confidence_scatter(),
        lambda: chart_association_rule_count_lines(assoc_grid),
    ):
        p = fn()
        created.append(p)
        print(p)

    print("提取特征重要性 ...")
    fi_data = extract_all_model_importances()

    for fn in (
        lambda: chart_feature_importance_top20(fi_data),
        lambda: chart_feature_importance_correlation(fi_data),
        lambda: chart_feature_importance_overlap(fi_data),
    ):
        p = fn()
        created.append(p)
        print(p)

    return created


if __name__ == "__main__":
    paths = generate_charts()
    print(f"\n共生成 {len(paths)} 张 PNG 图表")
