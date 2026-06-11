"""
招聘数据可视化 —— 从 output/ 读取 JSON 生成分析图表
输出到 output/charts/ 目录
"""

import json
import os
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # 无 GUI 后端，纯文件输出
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# ── 配置 ──────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).parent / "output"
CHART_DIR  = OUTPUT_DIR / "charts"
CHART_DIR.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.family":     "sans-serif",
    "font.sans-serif": ["SimHei", "Microsoft YaHei", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "figure.dpi":      150,
    "savefig.dpi":     150,
    "savefig.bbox":    "tight",
})

# ── 读取数据 ──────────────────────────────────────────
def load_all():
    rows = []
    for f in ["校招岗位.json", "社招岗位.json", "实习岗位.json"]:
        fp = OUTPUT_DIR / f
        if not fp.exists():
            continue
        with open(fp, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        print(f"  {f}: {len(data)} 条")
        rows.extend(data)
    return rows

print("读取数据...")
data = load_all()
print(f"  合计: {len(data)} 条\n")

# ── 辅助函数 ──────────────────────────────────────────
def top_n(counter, n=15):
    """返回 (labels, values) 前 N 项"""
    common = counter.most_common(n)
    if not common:
        return [], []
    labels, values = zip(*common)
    return list(labels), list(values)


def ci_counter(items):
    """忽略大小写、跳过空值的 Counter。items 为原始值迭代器"""
    c = Counter()
    for v in items:
        if v:
            v = v.strip()
            if v:
                c[v.lower()] += 1
    return c


def auto_barh(ax, labels, values, title, xlabel="数量", color="steelblue"):
    """横向条形图"""
    ypos = range(len(labels))
    ax.barh(ypos, values, color=color, height=0.6)
    ax.set_yticks(ypos)
    ax.set_yticklabels(labels, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel(xlabel, fontsize=8)
    ax.set_title(title, fontsize=10, fontweight="bold")
    for i, v in enumerate(values):
        ax.text(v + max(values) * 0.01, i, str(v), va="center", fontsize=6)


def auto_pie(ax, labels, values, title):
    """饼图"""
    wedges, texts, autotexts = ax.pie(
        values, labels=None, autopct="%1.1f%%",
        startangle=90, pctdistance=0.75,
        colors=sns.color_palette("Set2", len(labels)),
    )
    ax.set_title(title, fontsize=10, fontweight="bold")
    # 图例
    legend_labels = [f"{l} ({v})" for l, v in zip(labels, values)]
    ax.legend(
        wedges, legend_labels,
        title="类别", loc="center left",
        bbox_to_anchor=(1, 0, 0.5, 1),
        fontsize=6,
    )


# ── 通用字段提取 ──────────────────────────────────────
def extract_salary(row):
    """解析薪资，返回 (月薪下限, 月薪上限, 年薪万) 或 None"""
    try:
        lo = float(row.get("薪资下限", 0))
        hi = float(row.get("薪资上限", 0))
        months = float(row.get("薪资月数", 12))
    except (ValueError, TypeError):
        return None
    if lo <= 0 or hi > 1_000_000 or hi <= lo:
        return None
    return lo, hi, (lo + hi) / 2 * months / 10_000



# ══════════════════════════════════════════════════════
#  图 1：招聘类型分布
# ══════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(6, 4))
types = ci_counter(r.get("招聘类型") for r in data)
labels, values = top_n(types, 10)
auto_barh(ax, labels, values, "招聘类型分布", color="#4C72B0")
fig.tight_layout()
fig.savefig(CHART_DIR / "01_招聘类型分布.png")
plt.close(fig)
print("[OK] 01_招聘类型分布.png")

# ══════════════════════════════════════════════════════
#  图 2：搜索关键词分布（Top 15）
# ══════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(6, 5))
kw = ci_counter(r.get("搜索关键词") for r in data)
labels, values = top_n(kw, 15)
auto_barh(ax, labels, values, "搜索关键词 Top 15", color="#DD8452")
fig.tight_layout()
fig.savefig(CHART_DIR / "02_搜索关键词分布.png")
plt.close(fig)
print("[OK] 02_搜索关键词分布.png")

# ══════════════════════════════════════════════════════
#  图 3：工作城市分布（Top 15）
# ══════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(6, 5))
cities = ci_counter(r.get("工作城市") for r in data)
labels, values = top_n(cities, 15)
auto_barh(ax, labels, values, "工作城市 Top 15", color="#55A868")
fig.tight_layout()
fig.savefig(CHART_DIR / "03_工作城市分布.png")
plt.close(fig)
print("[OK] 03_工作城市分布.png")

# ══════════════════════════════════════════════════════
#  图 4：学历要求分布
# ══════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(7, 4))
edu = ci_counter(r.get("学历要求") for r in data)
# 按学历高低排序
edu_order = ["博士及以上", "硕士及以上", "硕士", "本科及以上", "本科", "大专及以上", "大专", "学历不限"]
edu_items = [(k, v) for k, v in edu.items()]
edu_order_lower = [x.lower() for x in edu_order]
edu_items.sort(key=lambda x: edu_order_lower.index(x[0]) if x[0] in edu_order_lower else 99)
labels, values = zip(*edu_items) if edu_items else ([], [])
auto_barh(ax, list(labels), list(values), "学历要求分布", color="#8172B2")
fig.tight_layout()
fig.savefig(CHART_DIR / "04_学历要求分布.png")
plt.close(fig)
print("[OK] 04_学历要求分布.png")

# ══════════════════════════════════════════════════════
#  图 5：公司规模分布
# ══════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(6, 4))
scale = ci_counter(r.get("公司规模") for r in data)
labels, values = top_n(scale, 10)
auto_barh(ax, labels, values, "公司规模分布", color="#C44E52")
fig.tight_layout()
fig.savefig(CHART_DIR / "05_公司规模分布.png")
plt.close(fig)
print("[OK] 05_公司规模分布.png")

# ══════════════════════════════════════════════════════
#  图 6：所属行业分布（Top 15）
# ══════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(6, 5))
ind = ci_counter(r.get("所属行业") for r in data)
labels, values = top_n(ind, 15)
auto_barh(ax, labels, values, "所属行业 Top 15", color="#937860")
fig.tight_layout()
fig.savefig(CHART_DIR / "06_所属行业分布.png")
plt.close(fig)
print("[OK] 06_所属行业分布.png")

# ══════════════════════════════════════════════════════════════════
#  图 7-12：薪资分布箱线图（6 个维度 × 月薪/日薪双子图）
# ══════════════════════════════════════════════════════════════════

# ── 有效薪资数据 ──────────────────────────────────
valid = []
for r in data:
    s = extract_salary(r)
    if s:
        valid.append({**r, "年薪(万)": s[2], "月薪下限": s[0], "月薪上限": s[1]})


def plot_salary_boxplot(dimension, group_field, filename):
    """2 子图（月薪/日薪），每组数据量 <30 不绘制"""
    monthly = {}
    daily = {}

    for r in valid:
        grp = (r.get(group_field) or "").strip().lower()
        if not grp:
            continue
        lo, hi = r["月薪下限"], r["月薪上限"]
        stype = (r.get("薪资类型") or "").strip()
        target = daily if stype == "日薪" else monthly
        target.setdefault(grp, []).append((lo + hi) / 2)

    monthly = dict(sorted(
        ((k, v) for k, v in monthly.items() if len(v) >= 30),
        key=lambda x: np.median(x[1]),
    ))
    daily = dict(sorted(
        ((k, v) for k, v in daily.items() if len(v) >= 30),
        key=lambda x: np.median(x[1]),
    ))

    panels = []
    if monthly:
        panels.append((monthly, "月薪", "月薪（千元/月）"))
    if daily:
        panels.append((daily, "日薪", "日薪（元/天）"))

    if not panels:
        print(f"  [SKIP] {filename}（所有组数据量均 <30）")
        return

    fig, axes = plt.subplots(1, len(panels), figsize=(6 * len(panels), 5))
    if len(panels) == 1:
        axes = [axes]

    for col, (sdata, stype_label, ylabel) in enumerate(panels):
        ax = axes[col]
        groups = list(sdata.keys())
        data_list = list(sdata.values())
        bp = ax.boxplot(data_list, tick_labels=groups, patch_artist=True, widths=0.5)
        for patch, color in zip(bp["boxes"], sns.color_palette("Set2", len(groups))):
            patch.set_facecolor(color)
        ax.set_title(f"{dimension} × {stype_label}分布", fontsize=10, fontweight="bold")
        ax.set_ylabel(ylabel, fontsize=8)
        ax.tick_params(axis="x", labelsize=7, rotation=30)
        ax.tick_params(axis="y", labelsize=7)

    fig.tight_layout()
    fig.savefig(CHART_DIR / filename)
    plt.close(fig)
    print(f"  [OK] {filename}")


plot_salary_boxplot("招聘类型", "招聘类型", "07_招聘类型_薪资分布.png")
plot_salary_boxplot("工作城市", "工作城市", "08_工作城市_薪资分布.png")
plot_salary_boxplot("搜索关键词", "搜索关键词", "09_搜索关键词_薪资分布.png")
plot_salary_boxplot("学历要求", "学历要求", "10_学历要求_薪资分布.png")
plot_salary_boxplot("所属行业", "所属行业", "11_所属行业_薪资分布.png")
plot_salary_boxplot("融资阶段", "融资阶段", "12_融资阶段_薪资分布.png")

# ══════════════════════════════════════════════════════════════════
#  图 13：Top 15 公司招聘岗位数
# ══════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(6, 5))
companies = ci_counter(r.get("公司名称") for r in data)
labels, values = top_n(companies, 15)
auto_barh(ax, labels, values, "招聘岗位数 Top 15 公司", color="#E5A262")
fig.tight_layout()
fig.savefig(CHART_DIR / "13_公司招聘岗位数.png")
plt.close(fig)
print("[OK] 13_公司招聘岗位数.png")

# ══════════════════════════════════════════════════════════════════
#  图 14：融资阶段分布
# ══════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(7, 4))
fund = ci_counter(r.get("融资阶段") for r in data)
# 排序：按融资阶段先后
fund_order = ["未融资", "天使轮", "A轮", "B轮", "C轮", "D轮及以上", "已上市"]
fund_order_lower = [x.lower() for x in fund_order]
fund_items = [(k, v) for k, v in fund.items()]
fund_items.sort(key=lambda x: fund_order_lower.index(x[0]) if x[0] in fund_order_lower else 99)
labels, values = zip(*fund_items) if fund_items else ([], [])
auto_barh(ax, list(labels), list(values), "融资阶段分布", color="#8DB6CE")
fig.tight_layout()
fig.savefig(CHART_DIR / "14_融资阶段分布.png")
plt.close(fig)
print("[OK] 14_融资阶段分布.png")

# ══════════════════════════════════════════════════════════════════
#  图 15：岗位标签词云（用条形图替代 Top 20 标签）
# ══════════════════════════════════════════════════════════════════
tags = []
for r in data:
    t = r.get("岗位标签", "")
    if t:
        tags.extend([x.strip().lower() for x in t.split(",") if x.strip()])
fig, ax = plt.subplots(figsize=(6, 6))
tag_counter = Counter(tags)
labels, values = top_n(tag_counter, 20)
auto_barh(ax, labels, values, "岗位标签 Top 20", color="#64B5CD")
fig.tight_layout()
fig.savefig(CHART_DIR / "15_岗位标签Top20.png")
plt.close(fig)
print("[OK] 15_岗位标签Top20.png")

# ══════════════════════════════════════════════════════════════════
#  图 16：各招聘类型的学历要求交叉分析（堆叠条形图）
# ══════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 4.5))
edu_levels = ["学历不限", "大专", "大专及以上", "本科", "本科及以上", "硕士", "硕士及以上", "博士及以上"]
type_order = ["实习", "校招", "社招"]
cross = {}
for t in type_order:
    cross[t] = ci_counter(r.get("学历要求") for r in data if r.get("招聘类型") == t)

x = np.arange(len(type_order))
width = 0.6
bottom = np.zeros(len(type_order))
colors = sns.color_palette("Set2", len(edu_levels))
color_map = {}
for i, edu in enumerate(edu_levels):
    vals = [cross[t].get(edu, 0) for t in type_order]
    if sum(vals) == 0:
        continue
    bars = ax.bar(x, vals, width, bottom=bottom, label=edu, color=colors[i % len(colors)])
    color_map[edu] = colors[i % len(colors)]
    bottom += np.array(vals)

ax.set_xticks(x)
ax.set_xticklabels(type_order, fontsize=8)
ax.set_title("招聘类型 × 学历要求 交叉分析", fontsize=10, fontweight="bold")
ax.legend(fontsize=6, loc="upper right")
fig.tight_layout()
fig.savefig(CHART_DIR / "16_招聘类型_学历交叉.png")
plt.close(fig)
print("[OK] 16_招聘类型_学历交叉.png")

# ══════════════════════════════════════════════════════════════════
#  图 17：Top 15 城市 × 平均薪资（气泡图）
# ══════════════════════════════════════════════════════════════════
city_salary = {}
for r in valid:
    city = (r.get("工作城市") or "").strip()
    if city:
        city_lower = city.lower()
        city_salary.setdefault(city_lower, []).append(r["年薪(万)"])
city_avg = {k: np.mean(v) for k, v in city_salary.items()}
city_count = ci_counter(r.get("工作城市") for r in data)
# 取岗位数最多的 15 个城市
top_cities = [c for c, _ in city_count.most_common(15)]
fig, ax = plt.subplots(figsize=(8, 5))
sizes = [city_count[c] * 15 for c in top_cities]
avg_sals = [city_avg.get(c, 0) for c in top_cities]
sc = ax.scatter(range(len(top_cities)), avg_sals, s=sizes, c=sizes,
                cmap="viridis", alpha=0.7, edgecolors="gray", linewidth=0.5)
ax.set_xticks(range(len(top_cities)))
ax.set_xticklabels(top_cities, fontsize=7, rotation=30, ha="right")
ax.set_ylabel("平均年薪（万元）", fontsize=8)
ax.set_title("Top 15 城市 · 岗位数(气泡大小) × 平均薪资", fontsize=10, fontweight="bold")
# 颜色条
cbar = fig.colorbar(sc, ax=ax, shrink=0.7)
cbar.set_label("岗位数", fontsize=7)
ax.tick_params(axis="y", labelsize=7)
fig.tight_layout()
fig.savefig(CHART_DIR / "17_城市薪资气泡图.png")
plt.close(fig)
print("[OK] 17_城市薪资气泡图.png")

total_charts = 11  # 6 salary boxplots + 5 remaining
print(f"\n完成！共生成 {total_charts} 张图表，保存至: {CHART_DIR}")
