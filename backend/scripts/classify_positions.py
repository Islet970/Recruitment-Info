"""Classify all positions by name using optimized regex rules, then update the database."""
import re, sys, os
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from app.core.database import SessionLocal
from app.models.category import JobCategory
from app.models.position import JobPosition

# ── Optimised category rules ─────────────────────────────────────────────────
# Order: most specific / narrow-match first, broad catch-all last.
# Each tuple: (regex_pattern, category_name)

CATEGORY_RULES = [
    # 1 人工智能 — AI/ML/DL/NLP/CV specific
    (r"AI(?!.*安全)|人工智能|大模型|LLM|机器学习|深度学习|自然语言|NLP|计算机视觉|多模态|SLAM|音视频.*算法|语音.*识别|AI.*Agent|AI.*搜索|AI.*推荐", "人工智能"),

    # 2 算法 — algorithm engineering (non-AI-general)
    (r"^算法工程师|算法.*工程师|搜推广|推荐.*算法|搜索.*算法|广告.*算法|图形学.*算法", "算法"),

    # 3 数据开发 — before 后端 so "Java+大数据" → 数据开发
    (r"大数据|数据仓库|ETL|数仓|数据工程师|数据开发|数据基础设施", "数据开发"),

    # 4 数据分析
    (r"数据分析|商业分析|BI|数据分析师|数据运营", "数据分析"),

    # 5 测试开发
    (r"测试|测开|QA|质量保障", "测试开发"),

    # 6 安全
    (r"安全|网络安全|信息安全", "安全"),

    # 7 前后端 → 全栈 (must be before 后端)
    (r"前后端", "全栈开发"),

    # 8 前端开发
    (r"前端|Vue|React|Web前端|H5|Web\s*前端", "前端开发"),

    # 9 后端开发 (broad — catches Java / C++ / Go / Python / cloud / etc.)
    (r"后端|Java(?!.*前端)|Go(?!.*前端)|C\s*\+\+|C\s*语言|Python(?!.*前端)|golang|云服务|云原生|阿里云|华为云|云网络|云产品|云安全|数据库|微服务|中间件|Kubernetes|容器|服务端|\.NET|基础设施.*研发|Agent.*(?:Infra|后端|开发)|存储|引擎", "后端开发"),

    # 10 运维开发
    (r"运维|SRE|DevOps|基础设施(?!研发)", "运维开发"),

    # 11 客户端开发
    (r"Android|iOS|客户端(?!.*前端)|PC端|pc端", "客户端开发"),

    # 12 全栈开发
    (r"全栈|全端", "全栈开发"),

    # 13 嵌入式 / 硬件
    (r"嵌入式|电源硬件|硬件开发|驱动开发|芯片|FPGA", "嵌入式开发"),

    # 14 产品类
    (r"产品经理|需求分析|产品.*岗位|产品.*方向", "产品类"),

    # 15 运营类
    (r"运营|新媒体|内容运营|用户运营", "运营类"),

    # 16 技术支持
    (r"技术支持|技术客服|helpdesk|售后技术", "技术支持"),

    # 17 设计类
    (r"UI|UX|交互设计|设计师", "设计类"),

    # 18 技术类 — catch-all for remaining tech positions
    (r"开发|研发|工程师|软件|技术|程序员|编码|工程", "技术类"),
]

# Categories in display order
CATEGORY_NAMES = [
    "人工智能", "算法", "后端开发", "前端开发", "数据开发", "数据分析",
    "测试开发", "运维开发", "客户端开发", "全栈开发", "嵌入式开发",
    "安全", "产品类", "运营类", "技术支持", "设计类", "技术类",
]


def classify(name: str) -> str | None:
    """Return the first matching category name, or None."""
    if not name or not name.strip():
        return None
    for pattern, category in CATEGORY_RULES:
        if re.search(pattern, name, re.IGNORECASE):
            return category
    return None


def main():
    db = SessionLocal()

    # ── 1. Clear old categories & insert new ones ──────────────────────
    print("Clearing old category references…")
    # Reset category_id on all positions first (FK constraint)
    db.query(JobPosition).update({"category_id": None}, synchronize_session="fetch")
    db.flush()

    # Remove old categories
    db.query(JobCategory).delete()
    db.flush()

    # Insert new categories
    print("Inserting new categories…")
    cat_objects = {}
    for i, name in enumerate(CATEGORY_NAMES):
        jc = JobCategory(name=name, sort_order=i)
        db.add(jc)
        db.flush()
        cat_objects[name] = jc.id

    # Also create "未分类" for unmatched positions
    jc_uncat = JobCategory(name="未分类", sort_order=99)
    db.add(jc_uncat)
    db.flush()
    cat_objects["未分类"] = jc_uncat.id

    db.commit()
    print(f"  Created {len(cat_objects)} categories: {list(cat_objects.keys())}")

    # ── 2. Classify all positions ──────────────────────────────────────
    positions = db.query(JobPosition).all()
    counter: Counter = Counter()
    unmatched: list[tuple[int, str]] = []

    for pos in positions:
        cat_name = classify(pos.name)
        if cat_name is None:
            cat_name = "未分类"
            unmatched.append((pos.id, pos.name))
        cat_id = cat_objects.get(cat_name)
        pos.category_id = cat_id
        counter[cat_name] += 1

    db.commit()

    # ── 3. Print summary ──────────────────────────────────────────────
    total = len(positions)
    print(f"\n{'='*50}")
    print(f"Classification complete - {total} positions")
    print(f"{'='*50}")
    for cat in CATEGORY_NAMES + ["未分类"]:
        cnt = counter.get(cat, 0)
        pct = cnt / total * 100 if total else 0
        bar_len = int(pct / 3.33)
        print(f"  {cat:12s} | {cnt:4d} ({pct:5.1f}%) {'#' * bar_len}")

    if unmatched:
        print(f"\n  {len(unmatched)} unmatched positions (-> wei fen lei):")
        for pid, pname in unmatched[:20]:
            print(f"    id={pid:4d}  {pname}")
        if len(unmatched) > 20:
            print(f"    ... and {len(unmatched) - 20} more")

    db.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
