"""
招聘数据可视化 2 —— 高级图表
从 output/ 读取 JSON，输出到 output/charts2/
"""

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MplPath
import numpy as np
import seaborn as sns

# ── 可选依赖 ─────────────────────────────────────────
try:
    import networkx as nx
    HAS_NX = True
except ImportError:
    HAS_NX = False

try:
    from statsmodels.graphics.mosaicplot import mosaic as sm_mosaic
    HAS_SM = True
except ImportError:
    HAS_SM = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    HAS_SK = True
except ImportError:
    HAS_SK = False

# ── 配置 ─────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).parent / "output"
CHART_DIR = OUTPUT_DIR / "charts2"
CHART_DIR.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.family":     "sans-serif",
    "font.sans-serif": ["SimHei", "Microsoft YaHei", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "figure.dpi":      150,
    "savefig.dpi":     150,
    "savefig.bbox":    "tight",
})

# 主要城市经纬度（用于图 9 散点"地图"）
CITY_COORDS = {
    "北京": (116.40, 39.90), "上海": (121.47, 31.23), "广州": (113.27, 23.13),
    "深圳": (114.06, 22.55), "杭州": (120.15, 30.27), "南京": (118.78, 32.05),
    "成都": (104.07, 30.67), "武汉": (114.31, 30.59), "西安": (108.94, 34.34),
    "重庆": (106.55, 29.56), "苏州": (120.59, 31.30), "天津": (117.20, 39.13),
    "长沙": (112.94, 28.23), "郑州": (113.62, 34.75), "青岛": (120.38, 36.07),
    "厦门": (118.10, 24.46), "合肥": (117.28, 31.86), "济南": (117.00, 36.65),
    "福州": (119.30, 26.08), "宁波": (121.55, 29.88), "无锡": (120.30, 31.57),
    "大连": (121.62, 38.92), "佛山": (113.12, 23.02), "东莞": (113.75, 23.05),
    "沈阳": (123.43, 41.80), "昆明": (102.71, 25.04), "石家庄": (114.51, 38.04),
    "太原": (112.55, 37.87), "长春": (125.32, 43.82), "哈尔滨": (126.53, 45.80),
    "海口": (110.35, 20.02), "南昌": (115.89, 28.68), "贵阳": (106.71, 26.57),
    "兰州": (103.83, 36.07), "南宁": (108.37, 22.82), "乌鲁木齐": (87.62, 43.83),
    "呼和浩特": (111.75, 40.84), "银川": (106.23, 38.49), "西宁": (101.78, 36.62),
    "拉萨": (91.11, 29.65), "香港": (114.16, 22.28), "澳门": (113.55, 22.20),
    "台北": (121.51, 25.05),
}


# ── 数据读取 & 清洗 ───────────────────────────────────
def load_all():
    rows = []
    for f in ["校招岗位.json", "社招岗位.json", "实习岗位.json"]:
        fp = OUTPUT_DIR / f
        if not fp.exists():
            continue
        with open(fp, "r", encoding="utf-8") as fh:
            rows.extend(json.load(fh))
    return rows


def monthly_mid(r):
    """有效月薪中位数；无效返回 None"""
    if (r.get("薪资类型") or "").strip() != "月薪":
        return None
    try:
        lo = float(r.get("薪资下限", 0))
        hi = float(r.get("薪资上限", 0))
    except (ValueError, TypeError):
        return None
    if lo <= 0 or hi <= lo or hi > 1_000_000:
        return None
    return (lo + hi) / 2


def top_n_keys(counter, n):
    return [k for k, _ in counter.most_common(n)]


# ══════════════════════════════════════════════════════
#  图 1：城市 × 招聘类型 薪资热力图
# ══════════════════════════════════════════════════════
def plot_01_city_type_heatmap(data):
    types = ["校招", "社招", "实习"]

    bucket = defaultdict(list)
    for r in data:
        c, t = r.get("工作城市"), r.get("招聘类型")
        if not c or t not in types:
            continue
        m = monthly_mid(r)
        if m is None:
            continue
        bucket[(c, t)].append(m)

    # 计算城市总样本数，只保留样本 ≥5 的城市
    city_counts = Counter()
    for (c, _), vals in bucket.items():
        city_counts[c] += len(vals)
    top_cities = [c for c, _ in city_counts.most_common(12) if city_counts[c] >= 5]
    if not top_cities:
        print("[SKIP] 01 数据不足")
        return

    # 只保留至少一个城市有数据的类型
    active_types = []
    for t in types:
        if any(len(bucket.get((c, t), [])) >= 3 for c in top_cities):
            active_types.append(t)

    salary_grid = np.full((len(top_cities), len(active_types)), np.nan)
    count_grid = np.zeros((len(top_cities), len(active_types)), dtype=int)

    for i, c in enumerate(top_cities):
        for j, t in enumerate(active_types):
            vals = bucket.get((c, t), [])
            if len(vals) >= 3:
                salary_grid[i, j] = np.median(vals)
                count_grid[i, j] = len(vals)

    # 动态尺寸
    fig_h = max(6, len(top_cities) * 0.55)
    fig, ax = plt.subplots(figsize=(max(5, len(active_types) * 1.6), fig_h))
    annot = np.array([[f"{salary_grid[i,j]:.0f}K\nn={count_grid[i,j]}" if count_grid[i,j] else ""
                      for j in range(len(active_types))] for i in range(len(top_cities))])
    mask = np.isnan(salary_grid)

    sns.heatmap(
        salary_grid, ax=ax, cmap="YlOrRd", mask=mask,
        xticklabels=active_types, yticklabels=top_cities,
        annot=annot, fmt="", annot_kws={"fontsize": 8},
        cbar_kws={"label": "中位月薪 (K)"},
        linewidths=0.5, linecolor="white",
    )
    ax.set_title("城市 × 招聘类型 中位月薪", fontsize=11, fontweight="bold")
    ax.tick_params(axis="y", labelsize=9)
    fig.tight_layout()
    fig.savefig(CHART_DIR / "01_城市_类型_薪资热力图.png")
    plt.close(fig)
    print("[OK] 01_城市_类型_薪资热力图.png")


# ══════════════════════════════════════════════════════
#  图 2：学历 × 融资阶段 薪资矩阵
# ══════════════════════════════════════════════════════
def plot_02_edu_funding_matrix(data):
    edu_order = ["学历不限", "大专", "大专及以上", "本科", "本科及以上",
                 "硕士", "硕士及以上", "博士及以上"]
    fund_order = ["未融资", "天使轮", "A轮", "B轮", "C轮", "D轮及以上", "已上市"]

    bucket = defaultdict(list)
    for r in data:
        e = (r.get("学历要求") or "").strip()
        f = (r.get("融资阶段") or "").strip()
        if e not in edu_order or f not in fund_order:
            continue
        m = monthly_mid(r)
        if m is None:
            continue
        bucket[(e, f)].append(m)

    # 过滤：只保留至少有 1 个格 ≥3 样本的行/列
    active_edu = []
    for e in edu_order:
        if any(len(bucket.get((e, f), [])) >= 3 for f in fund_order):
            active_edu.append(e)
    active_fund = []
    for f in fund_order:
        if any(len(bucket.get((e, f), [])) >= 3 for e in active_edu):
            active_fund.append(f)

    if not active_edu or not active_fund:
        print("[SKIP] 02 数据不足")
        return

    grid = np.full((len(active_edu), len(active_fund)), np.nan)
    counts = np.zeros_like(grid, dtype=int)
    for i, e in enumerate(active_edu):
        for j, f in enumerate(active_fund):
            vals = bucket.get((e, f), [])
            if len(vals) >= 3:
                grid[i, j] = np.median(vals)
                counts[i, j] = len(vals)

    fig_h = max(5, len(active_edu) * 0.55)
    fig, ax = plt.subplots(figsize=(max(7, len(active_fund) * 1.2), fig_h))
    annot = np.array([[f"{grid[i,j]:.0f}K\nn={int(counts[i,j])}" if counts[i,j] else ""
                      for j in range(len(active_fund))] for i in range(len(active_edu))])
    mask = np.isnan(grid)
    sns.heatmap(
        grid, ax=ax, cmap="viridis", mask=mask,
        xticklabels=active_fund, yticklabels=active_edu,
        annot=annot, fmt="", annot_kws={"fontsize": 7},
        cbar_kws={"label": "中位月薪 (K)"},
        linewidths=0.5, linecolor="white",
    )
    ax.set_title("学历 × 融资阶段 中位月薪", fontsize=11, fontweight="bold")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=9)
    plt.setp(ax.get_yticklabels(), fontsize=9)
    fig.tight_layout()
    fig.savefig(CHART_DIR / "02_学历_融资阶段_薪资矩阵.png")
    plt.close(fig)
    print("[OK] 02_学历_融资阶段_薪资矩阵.png")


# ══════════════════════════════════════════════════════
#  图 3：城市 → 行业 桑基图（手绘版）
# ══════════════════════════════════════════════════════
def plot_03_city_industry_sankey(data):
    flows = Counter()
    for r in data:
        c = (r.get("工作城市") or "").strip()
        ind = (r.get("所属行业") or "").strip()
        if c and ind:
            flows[(c, ind)] += 1

    top_cities = top_n_keys(Counter(c for (c, _), v in flows.items() for _ in range(v)), 8)
    top_inds = top_n_keys(Counter(i for (_, i), v in flows.items() for _ in range(v)), 8)

    pairs = [((c, i), v) for (c, i), v in flows.items() if c in top_cities and i in top_inds]
    if not pairs:
        print("[SKIP] 03 数据不足")
        return

    # 合并小流向（< 总量 0.5%）到"其他行业"
    total = sum(v for _, v in pairs)
    min_thresh = total * 0.005
    small_pairs = [(k, v) for k, v in pairs if v < min_thresh]
    if len(small_pairs) > 1:
        for k, _ in small_pairs:
            pairs.remove((k, _))
        merged = sum(v for _, v in small_pairs)
        pairs.append((("其他", "其他"), merged))
        if "其他" not in top_cities:
            top_cities.append("其他")
        if "其他" not in top_inds:
            top_inds.append("其他")

    city_total = {c: sum(v for (cc, _), v in pairs if cc == c) for c in top_cities}
    ind_total = {i: sum(v for (_, ii), v in pairs if ii == i) for i in top_inds}
    top_cities = [c for c in top_cities if city_total.get(c, 0) > 0]
    top_inds = [i for i in top_inds if ind_total.get(i, 0) > 0]

    fig, ax = plt.subplots(figsize=(12, max(7, len(top_cities) * 0.8)))
    ax.set_xlim(0, 10)
    total = sum(city_total[c] for c in top_cities)
    ax.set_ylim(-total * 0.02, total * 1.02)
    ax.axis("off")

    gap = total * 0.04  # 增大间距
    block_w = 0.35

    city_starts = {}
    y = total
    for c in top_cities:
        h = city_total[c]
        city_starts[c] = (y - h, y)
        ax.add_patch(plt.Rectangle((0.5, y - h), block_w, h,
                                   color=sns.color_palette("Set2")[0], alpha=0.85))
        ax.text(0.45, y - h / 2, f"{c} ({h})", ha="right", va="center", fontsize=8)
        y -= h + gap

    ind_starts = {}
    y = total
    for i in top_inds:
        h = ind_total[i]
        ind_starts[i] = (y - h, y)
        ax.add_patch(plt.Rectangle((9.65 - block_w, y - h), block_w, h,
                                   color=sns.color_palette("Set2")[1], alpha=0.85))
        ax.text(9.7, y - h / 2, f"{i} ({h})", ha="left", va="center", fontsize=8)
        y -= h + gap

    city_used = {c: city_starts[c][1] for c in top_cities}
    ind_used = {i: ind_starts[i][1] for i in top_inds}
    colors = sns.color_palette("husl", len(top_cities))
    city_color = dict(zip(top_cities, colors))

    pairs.sort(key=lambda x: top_cities.index(x[0][0]))
    for (c, i), v in pairs:
        y0_top = city_used[c]
        y0_bot = y0_top - v
        city_used[c] = y0_bot
        y1_top = ind_used[i]
        y1_bot = y1_top - v
        ind_used[i] = y1_bot

        x0 = 0.5 + block_w
        x1 = 9.65 - block_w
        cx = (x0 + x1) / 2
        verts = [
            (x0, y0_top), (cx, y0_top), (cx, y1_top), (x1, y1_top),
            (x1, y1_bot), (cx, y1_bot), (cx, y0_bot), (x0, y0_bot),
            (x0, y0_top),
        ]
        codes = [MplPath.MOVETO,
                 MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
                 MplPath.LINETO,
                 MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
                 MplPath.CLOSEPOLY]
        path = MplPath(verts, codes)
        patch = PathPatch(path, facecolor=city_color[c], alpha=0.35, edgecolor="none")
        ax.add_patch(patch)

    ax.set_title("城市 → 行业 岗位流向（Top 8）", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(CHART_DIR / "03_城市_行业_桑基图.png")
    plt.close(fig)
    print("[OK] 03_城市_行业_桑基图.png")


# ══════════════════════════════════════════════════════
#  图 4：招聘类型 薪资小提琴图 + 散点
# ══════════════════════════════════════════════════════
def plot_04_violin_by_type(data):
    types = ["实习", "校招", "社招"]
    buckets = {t: [] for t in types}
    for r in data:
        t = r.get("招聘类型")
        if t in buckets:
            m = monthly_mid(r)
            if m is not None:
                buckets[t].append(m)

    types = [t for t in types if len(buckets[t]) >= 5]
    if not types:
        print("[SKIP] 04 数据不足")
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    parts = ax.violinplot([buckets[t] for t in types], showmedians=True, widths=0.8)
    for i, pc in enumerate(parts["bodies"]):
        pc.set_facecolor(sns.color_palette("Set2")[i])
        pc.set_alpha(0.6)

    rng = np.random.default_rng(42)
    for i, t in enumerate(types, start=1):
        vals = buckets[t]
        # 抽样防过密
        if len(vals) > 500:
            vals = list(rng.choice(vals, 500, replace=False))
        x = rng.normal(i, 0.05, size=len(vals))
        ax.scatter(x, vals, s=4, alpha=0.3, color="black")

    ax.set_xticks(range(1, len(types) + 1))
    ax.set_xticklabels(types, fontsize=10)
    ax.set_ylabel("月薪中位 (K)")
    ax.set_title("招聘类型 薪资分布（小提琴 + 散点）", fontsize=11, fontweight="bold")
    all_vals = [v for vals in buckets.values() for v in vals]
    if all_vals:
        ax.set_ylim(bottom=max(-0.5, np.percentile(all_vals, 1) * 0.9),
                    top=np.percentile(all_vals, 99) * 1.1)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(CHART_DIR / "04_招聘类型_薪资小提琴图.png")
    plt.close(fig)
    print("[OK] 04_招聘类型_薪资小提琴图.png")


# ══════════════════════════════════════════════════════
#  图 5：公司规模 × 薪资 气泡图（颜色=融资阶段）
# ══════════════════════════════════════════════════════
def plot_05_scale_salary_bubble(data):
    scale_order = ["少于15人", "15-50人", "50-150人", "150-500人",
                   "500-2000人", "2000-10000人", "10000人以上"]
    fund_order = ["未融资", "天使轮", "A轮", "B轮", "C轮", "D轮及以上", "已上市"]

    bucket = defaultdict(list)
    for r in data:
        s = (r.get("公司规模") or "").strip()
        f = (r.get("融资阶段") or "").strip()
        if s not in scale_order or f not in fund_order:
            continue
        m = monthly_mid(r)
        if m is None:
            continue
        bucket[(s, f)].append(m)

    # 过滤无数据的行/列
    active_scale = []
    for s in scale_order:
        if any(len(bucket.get((s, f), [])) >= 3 for f in fund_order):
            active_scale.append(s)
    active_fund = []
    for f in fund_order:
        if any(len(bucket.get((s, f), [])) >= 3 for s in active_scale):
            active_fund.append(f)

    if not active_scale or not active_fund:
        print("[SKIP] 05 数据不足")
        return

    fig, ax = plt.subplots(figsize=(max(10, len(active_scale) * 1.5), 6))
    cmap = sns.color_palette("husl", len(active_fund))

    # 使用轻微的 x 偏移避免同列重叠
    offset = np.linspace(-0.12, 0.12, len(active_fund))
    for j, f in enumerate(active_fund):
        xs, ys, sizes = [], [], []
        for i, s in enumerate(active_scale):
            vals = bucket.get((s, f), [])
            if len(vals) >= 3:
                xs.append(i + offset[j])
                ys.append(np.median(vals))
                sizes.append(len(vals))
        if xs:
            ax.scatter(xs, ys, s=[max(30, n * 2.5) for n in sizes],
                       color=cmap[j], alpha=0.65, label=f,
                       edgecolors="white", linewidths=0.5)

    ax.set_xticks(range(len(active_scale)))
    ax.set_xticklabels(active_scale, rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("中位月薪 (K)")
    ax.set_xlabel("公司规模")
    ax.set_title("公司规模 × 中位月薪（气泡=岗位数，颜色=融资阶段）",
                 fontsize=11, fontweight="bold")
    ax.legend(fontsize=7, loc="upper left", title="融资阶段",
              ncol=2, framealpha=0.8)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(CHART_DIR / "05_公司规模_薪资_气泡图.png")
    plt.close(fig)
    print("[OK] 05_公司规模_薪资_气泡图.png")


# ══════════════════════════════════════════════════════
#  图 6：岗位标签共现网络
# ══════════════════════════════════════════════════════
def plot_06_tag_network(data):
    if not HAS_NX:
        print("[SKIP] 06 需要 networkx，运行: pip install networkx")
        return

    tag_count = Counter()
    co_count = Counter()
    for r in data:
        raw = r.get("岗位标签", "") or ""
        tags = [t.strip().lower() for t in raw.split(",") if t.strip()]
        tags = list(dict.fromkeys(tags))
        for t in tags:
            tag_count[t] += 1
        for i in range(len(tags)):
            for j in range(i + 1, len(tags)):
                a, b = sorted([tags[i], tags[j]])
                co_count[(a, b)] += 1

    top = [t for t, _ in tag_count.most_common(20)]
    top_set = set(top)
    edges = [(a, b, w) for (a, b), w in co_count.items()
             if a in top_set and b in top_set and w >= 2]
    if not edges:
        print("[SKIP] 06 共现边不足")
        return

    G = nx.Graph()
    for t in top:
        G.add_node(t, size=tag_count[t])
    for a, b, w in edges:
        G.add_edge(a, b, weight=w)

    fig, ax = plt.subplots(figsize=(13, 10))

    # 使用 spring_layout 更大间距，更多迭代稳定布局
    pos = nx.spring_layout(G, k=2.5, seed=42, iterations=200)

    node_sizes = [max(80, tag_count.get(n, 1) * 30) for n in G.nodes()]
    edge_widths = [max(0.3, G[a][b]["weight"] * 0.5) for a, b in G.edges()]

    nx.draw_networkx_edges(G, pos, ax=ax, width=edge_widths,
                           edge_color="gray", alpha=0.35)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=node_sizes,
                           node_color=sns.color_palette("Set2")[2],
                           alpha=0.85, edgecolors="white", linewidths=0.5)

    # 标签轻微偏移以避免与节点重叠
    label_pos = {k: (x, y + 0.02) for k, (x, y) in pos.items()}
    nx.draw_networkx_labels(G, label_pos, ax=ax, font_size=7,
                            font_family="SimHei")
    ax.set_title("岗位标签共现网络（节点大小=频次，连线粗细=共现次数）",
                 fontsize=11, fontweight="bold")
    ax.axis("off")
    ax.set_xlim(ax.get_xlim()[0] - 0.2, ax.get_xlim()[1] + 0.2)
    ax.set_ylim(ax.get_ylim()[0] - 0.1, ax.get_ylim()[1] + 0.1)
    fig.tight_layout()
    fig.savefig(CHART_DIR / "06_岗位标签共现网络.png")
    plt.close(fig)
    print("[OK] 06_岗位标签共现网络.png")


# ══════════════════════════════════════════════════════
#  图 7：Top 公司 中位月薪 + P25-P75 误差棒
# ══════════════════════════════════════════════════════
def plot_07_company_salary_ranking(data):
    bucket = defaultdict(list)
    for r in data:
        c = (r.get("公司名称") or "").strip()
        if not c:
            continue
        m = monthly_mid(r)
        if m is not None:
            bucket[c].append(m)

    qualified = [(c, vals) for c, vals in bucket.items() if len(vals) >= 5]
    if not qualified:
        print("[SKIP] 07 无公司样本数 ≥5")
        return

    qualified.sort(key=lambda x: np.median(x[1]), reverse=True)
    top = qualified[:15]

    names = [c for c, _ in top]
    meds = [np.median(v) for _, v in top]
    p25 = [np.percentile(v, 25) for _, v in top]
    p75 = [np.percentile(v, 75) for _, v in top]
    err_lo = [m - lo for m, lo in zip(meds, p25)]
    err_hi = [hi - m for m, hi in zip(meds, p75)]
    nums = [len(v) for _, v in top]

    fig, ax = plt.subplots(figsize=(8, 6))
    y = range(len(names))
    ax.errorbar(meds, y, xerr=[err_lo, err_hi], fmt="o",
                color="#C44E52", ecolor="gray", capsize=4, markersize=7)
    # 样本数放 tick label 避免与误差棒重叠
    ax.set_yticks(list(y))
    ax.set_yticklabels([f"{n}  (n={c})" for n, c in zip(names, nums)], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("月薪 (K)")
    ax.set_title("Top 15 公司中位月薪 + P25-P75（仅样本数 ≥5）",
                 fontsize=11, fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    # 在条形右侧标注中位值
    for i, (m, _) in enumerate(zip(meds, names)):
        ax.text(m + 0.3, i, f"{m:.1f}K", va="center", fontsize=7, color="#C44E52", fontweight="bold")
    fig.tight_layout()
    fig.savefig(CHART_DIR / "07_公司薪资排行.png")
    plt.close(fig)
    print("[OK] 07_公司薪资排行.png")


# ══════════════════════════════════════════════════════
#  图 8：招聘类型 × 学历 马赛克图
# ══════════════════════════════════════════════════════
def plot_08_type_edu_mosaic(data):
    if not HAS_SM:
        print("[SKIP] 08 需要 statsmodels，运行: pip install statsmodels")
        return

    edu_keep = {"学历不限", "大专", "本科", "硕士", "博士及以上",
                "大专及以上", "本科及以上", "硕士及以上"}
    type_order = ["实习", "校招", "社招"]

    counter = Counter()
    for r in data:
        t = r.get("招聘类型")
        e = (r.get("学历要求") or "").strip()
        if t in type_order and e in edu_keep:
            counter[(t, e)] += 1

    if not counter:
        print("[SKIP] 08 数据不足")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    edu_set = sorted({e for _, e in counter})
    palette = sns.color_palette("Set2", len(edu_set))
    color_map = {e: palette[i] for i, e in enumerate(edu_set)}
    props = lambda key: {"color": color_map.get(key[1], "lightgray"), "alpha": 0.75}
    label_short = lambda key: key[1]

    sm_mosaic(counter, ax=ax, properties=props, labelizer=label_short,
              gap=0.015, title="")
    ax.set_title("招聘类型 × 学历要求 马赛克图", fontsize=11, fontweight="bold")
    fig.tight_layout()
    fig.savefig(CHART_DIR / "08_招聘类型_学历_马赛克.png")
    plt.close(fig)
    print("[OK] 08_招聘类型_学历_马赛克.png")


# ══════════════════════════════════════════════════════
#  图 9：城市分布"地图"散点
# ══════════════════════════════════════════════════════
def plot_09_city_geo(data):
    bucket = defaultdict(list)
    for r in data:
        c = (r.get("工作城市") or "").strip()
        if c not in CITY_COORDS:
            continue
        m = monthly_mid(r)
        bucket[c].append(m)

    if not bucket:
        print("[SKIP] 09 无可定位城市")
        return

    cities = list(bucket.keys())
    lons = [CITY_COORDS[c][0] for c in cities]
    lats = [CITY_COORDS[c][1] for c in cities]
    counts = [len(bucket[c]) for c in cities]
    valid_med = [np.median([v for v in bucket[c] if v is not None])
                 if any(v is not None for v in bucket[c]) else np.nan
                 for c in cities]

    fig, ax = plt.subplots(figsize=(11, 8))
    ax.set_facecolor("#f4f4f4")

    sizes = [max(40, c * 4) for c in counts]
    valid = ~np.isnan(valid_med)
    sc = ax.scatter(np.array(lons)[valid], np.array(lats)[valid],
                    s=np.array(sizes)[valid], c=np.array(valid_med)[valid],
                    cmap="YlOrRd", alpha=0.7, edgecolors="black", linewidths=0.5)
    if (~valid).any():
        ax.scatter(np.array(lons)[~valid], np.array(lats)[~valid],
                   s=np.array(sizes)[~valid], color="lightgray",
                   alpha=0.5, edgecolors="black", linewidths=0.3)

    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label("中位月薪 (K)")

    # 仅给岗位数 Top 15 标注，简单防重叠
    top_idx = sorted(range(len(cities)), key=lambda i: counts[i], reverse=True)[:15]
    offsets = {}
    rng = np.random.default_rng(42)
    for i in top_idx:
        base_x, base_y = lons[i], lats[i]
        # 尝试多个偏移距离找到不重叠的位置
        best_off = (6, 4)
        for attempt in range(20):
            angle = rng.uniform(0, 2 * np.pi)
            dist = 4 + attempt * 1.2
            off_x = dist * np.cos(angle)
            off_y = dist * np.sin(angle)
            ok = True
            for j, (ox, oy) in offsets.items():
                if abs((base_x + off_x / 5) - ox) < 0.8 and abs((base_y + off_y / 5) - oy) < 0.8:
                    ok = False
                    break
            if ok:
                best_off = (off_x, off_y)
                break
        offsets[i] = (base_x + best_off[0] / 5, base_y + best_off[1] / 5)
        ax.annotate(f"{cities[i]}",
                    (lons[i], lats[i]),
                    xytext=best_off, textcoords="offset points",
                    fontsize=6.5, alpha=0.9,
                    arrowprops=dict(arrowstyle="->", color="gray", alpha=0.4, lw=0.5))

    ax.set_xlim(70, 140)
    ax.set_ylim(15, 55)
    ax.set_xlabel("经度")
    ax.set_ylabel("纬度")
    ax.set_title("城市岗位分布（点大小=岗位数，颜色=中位月薪）",
                 fontsize=11, fontweight="bold")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(CHART_DIR / "09_城市分布地图.png")
    plt.close(fig)
    print("[OK] 09_城市分布地图.png")


# ══════════════════════════════════════════════════════
#  图 10：岗位标签 TF-IDF Top 短语（按招聘类型分组）
# ══════════════════════════════════════════════════════
def plot_10_tag_tfidf(data):
    if not HAS_SK:
        print("[SKIP] 10 需要 scikit-learn，运行: pip install scikit-learn")
        return

    type_order = ["实习", "校招", "社招"]
    docs, labels = [], []
    for t in type_order:
        joined = []
        for r in data:
            if r.get("招聘类型") != t:
                continue
            tags = (r.get("岗位标签") or "").replace(",", " ").strip()
            if tags:
                joined.append(tags.lower())
        if joined:
            docs.append(" ".join(joined))
            labels.append(t)

    if len(docs) < 2:
        print("[SKIP] 10 文档不足")
        return

    vec = TfidfVectorizer(token_pattern=r"\S+", max_features=2000)
    M = vec.fit_transform(docs)
    feat = np.array(vec.get_feature_names_out())

    fig, axes = plt.subplots(1, len(labels), figsize=(5 * len(labels), 6), sharey=False)
    if len(labels) == 1:
        axes = [axes]

    palette = sns.color_palette("Set2", len(labels))
    for i, t in enumerate(labels):
        scores = M[i].toarray().flatten()
        idx = np.argsort(scores)[::-1][:15]
        words = feat[idx][::-1]
        vals = scores[idx][::-1]
        ax = axes[i]
        ax.barh(range(len(words)), vals, color=palette[i])
        ax.set_yticks(range(len(words)))
        ax.set_yticklabels(words, fontsize=8)
        ax.set_title(f"{t} 区分度 Top 15", fontsize=10, fontweight="bold")
        ax.set_xlabel("TF-IDF")

    fig.suptitle("各招聘类型 TF-IDF 关键标签", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(CHART_DIR / "10_岗位标签TFIDF.png")
    plt.close(fig)
    print("[OK] 10_岗位标签TFIDF.png")


# ══════════════════════════════════════════════════════
if __name__ == "__main__":
    print("读取数据...")
    data = load_all()
    print(f"  合计: {len(data)} 条\n")

    plotters = [
        plot_01_city_type_heatmap,
        plot_02_edu_funding_matrix,
        plot_03_city_industry_sankey,
        plot_04_violin_by_type,
        plot_05_scale_salary_bubble,
        plot_06_tag_network,
        plot_07_company_salary_ranking,
        plot_08_type_edu_mosaic,
        plot_09_city_geo,
        plot_10_tag_tfidf,
    ]
    for fn in plotters:
        try:
            fn(data)
        except Exception as e:
            print(f"[FAIL] {fn.__name__}: {e}")

    print(f"\n完成！输出至: {CHART_DIR}")
