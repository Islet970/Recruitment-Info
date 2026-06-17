"""
招聘数据可视化 —— 从 output/ 读取 JSON 生成分析图表
输出到 output/charts/ 目录
"""

import json
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from wordcloud import WordCloud

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


# ══════════════════════════════════════════════════════
#  图 1：招聘类型分布（饼图）
# ══════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(7, 5))
types = ci_counter(r.get("招聘类型") for r in data)
labels, values = top_n(types, 10)
auto_pie(ax, labels, values, "招聘类型分布")
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
#  图 3：工作城市分布（饼图）
# ══════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 6))
cities = ci_counter(r.get("工作城市") for r in data)
labels, values = top_n(cities, 15)
auto_pie(ax, labels, values, "工作城市 Top 15")
fig.tight_layout()
fig.savefig(CHART_DIR / "03_工作城市分布.png")
plt.close(fig)
print("[OK] 03_工作城市分布.png")

# ══════════════════════════════════════════════════════
#  图 4：学历要求分布（饼图）
# ══════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 6))
edu = ci_counter(r.get("学历要求") for r in data)
# 按学历高低排序
edu_order = ["博士及以上", "硕士及以上", "硕士", "本科及以上", "本科", "大专及以上", "大专", "学历不限"]
edu_items = [(k, v) for k, v in edu.items()]
edu_order_lower = [x.lower() for x in edu_order]
edu_items.sort(key=lambda x: edu_order_lower.index(x[0]) if x[0] in edu_order_lower else 99)
labels, values = zip(*edu_items) if edu_items else ([], [])
auto_pie(ax, list(labels), list(values), "学历要求分布")
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

def plot_salary_boxplot(dimension, group_field, filename):
    """2 子图（月薪/日薪），每组数据量 <30 不绘制"""
    monthly, daily = {}, {}

    for r in data:
        try:
            lo = float(r.get("薪资下限", 0))
            hi = float(r.get("薪资上限", 0))
        except (ValueError, TypeError):
            continue
        if lo <= 0 or hi <= lo or hi > 1_000_000:
            continue

        grp = (r.get(group_field) or "").strip().lower()
        if not grp:
            continue

        target = daily if (r.get("薪资类型") or "").strip() == "日薪" else monthly
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
#  图 15：岗位标签词云
# ══════════════════════════════════════════════════════════════════
tag_counter = Counter()
tag_display = {}
for r in data:
    t = r.get("岗位标签", "")
    if t:
        for x in t.split(","):
            x = x.strip()
            if x:
                key = x.lower()
                tag_counter[key] += 1
                tag_display.setdefault(key, x)
tags = {tag_display[k]: v for k, v in tag_counter.items()}
fig, ax = plt.subplots(figsize=(12, 8))
if tags:
    wc = WordCloud(
        font_path="C:/Windows/Fonts/simhei.ttf",
        width=1200, height=800,
        background_color="white",
        max_words=30,
        colormap="Set2",
        random_state=42,
        regexp=r"\S+",
    ).generate_from_frequencies(tags)
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title("岗位标签词云", fontsize=14, fontweight="bold")
else:
    ax.text(0.5, 0.5, "无标签数据", ha="center", va="center", fontsize=14)
    ax.set_title("岗位标签词云（无数据）", fontsize=14, fontweight="bold")
fig.tight_layout()
fig.savefig(CHART_DIR / "15_岗位标签词云.png")
plt.close(fig)
print("[OK] 15_岗位标签词云.png")

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



total_charts = 16  # 6 salary boxplots + 5 remaining
print(f"\n完成！共生成 {total_charts} 张图表，保存至: {CHART_DIR}")
