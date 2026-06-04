#!/usr/bin/env python3
"""
牛客网杭州地区计算机岗位招聘信息爬虫 + 数据库导入
=====================================================
技术栈覆盖:
  (1) requests       — 直接 HTTP 请求获取岗位列表 JSON + 公司详情 JSON
  (2) Playwright     — 浏览器自动化，打开公司页面获取公司介绍
  (3) BeautifulSoup  — 解析公司页面 HTML
  (4) 正则表达式     — 文本清洗、HTML 标签剥离
  (5) JSON           — 数据保存
  (6) 数据库导入     — 爬取结果写入 SQLite

爬取: 28 种计算机岗位 × 校招/实习/社招
输出: output/{校招,实习,社招}岗位.json + 导入数据库
"""

import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# ==================== Windows 编码 ====================
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ==================== 配置 ====================
JOB_KEYWORDS = [
    "Java", "C++", "PHP", "golang", "安全工程师", "游戏后端", "区块链",
    "信息技术岗", "C 工程师", "C# 工程师", ".NET", "Python", "Delphi",
    "GIS 工程师", "VB", "Perl", "Ruby", "Node.js", "Erlang", "后端工程师",
    "语音/视频/图形开发", "全栈开发", "前端工程师", "Web 前端",
    "前端开发其它", "游戏前端", "HTML5", "UI设计师", "交互设计师",
]

RECRUIT_TYPES = [
    {"name": "校招", "recruit_type": 1},
    {"name": "实习", "recruit_type": 2},
    {"name": "社招", "recruit_type": 3},
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

LIST_API = "https://www.nowcoder.com/np-api/u/job/square-search"
COMPANY_API = "https://www.nowcoder.com/np-api/u/company/detail"
BASE_URL = "https://www.nowcoder.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.nowcoder.com/jobs/intern/center",
    "Content-Type": "application/x-www-form-urlencoded",
}


# ==================== 工具函数 ====================

def html_to_text(html_str):
    """正则表达式：剥离 HTML 标签"""
    if not html_str:
        return ""
    text = re.sub(r"<[^>]+>", "", html_str)
    for entity, char in [("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"),
                         ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'")]:
        text = text.replace(entity, char)
    return re.sub(r"\n\s*\n", "\n", text).strip()


def bs_html_to_text(html_str):
    """BeautifulSoup：将 HTML 转为纯文本"""
    if not html_str:
        return ""
    return BeautifulSoup(html_str, "html.parser").get_text(separator="\n").strip()


def parse_ext(ext_str):
    """解析 ext JSON 字段，提取岗位职责、岗位要求、加分项"""
    infos = requirements = bonus = ""
    if not ext_str:
        return infos, requirements, bonus
    try:
        ext_data = json.loads(ext_str)
        infos = ext_data.get("infos", "") or ""
        requirements = ext_data.get("requirements", "") or ""
        bonus_keywords = ["加分", "优先", "具备以下条件", "有以下经验", "优先考虑"]
        bonus_lines = [l for l in requirements.split("\n") if l.strip()
                       and any(kw in l for kw in bonus_keywords)]
        other_lines = [l for l in requirements.split("\n") if l.strip()
                       and l not in bonus_lines]
        if bonus_lines:
            bonus = "\n".join(bonus_lines)
            requirements = "\n".join(other_lines)
    except (json.JSONDecodeError, TypeError):
        requirements = ext_str or ""
    return infos.strip(), requirements.strip(), bonus.strip()


def format_salary(job):
    """格式化薪资"""
    st, smin, smax, smon = (job.get(k, 0) for k in
                            ["salaryType", "salaryMin", "salaryMax", "salaryMonth"])
    if smin == 0 and (smax == 0 or smax >= 999999):
        return "薪资面议"
    if st == 1:
        return f"{smin}-{smax}元/天"
    base = f"{smin}-{smax}K"
    return f"{base} * {smon}薪" if smon else base


def parse_job_item(data, keyword, recruit_name):
    """将 API 返回的原始数据转为统一字典"""
    ext_str = data.get("ext", "")
    infos, requirements, bonus = parse_ext(ext_str)
    company = data.get("recommendInternCompany", {}) or {}
    boss = data.get("apiSimpleBossUser", {}) or {}

    edu_map = {5000: "本科及以上", 4000: "大专及以上", 6000: "硕士及以上",
               7000: "博士及以上", 0: "学历不限"}

    return {
        "搜索关键词": keyword,
        "招聘类型": recruit_name,
        "岗位ID": data.get("id", ""),
        "岗位名称": data.get("jobName", ""),
        "岗位链接": f"https://www.nowcoder.com/jobs/detail/{data.get('id', '')}",
        "工作城市": data.get("jobCity", ""),
        "工作地址": data.get("jobAddress", ""),
        "岗位标签": data.get("jobKeys", ""),
        "薪资": format_salary(data),
        "薪资类型": "日薪" if data.get("salaryType") == 1 else "月薪",
        "薪资下限": data.get("salaryMin", 0),
        "薪资上限": data.get("salaryMax", 0),
        "薪资月数": data.get("salaryMonth", 0),
        "学历要求": edu_map.get(data.get("eduLevel", 0), "学历不限"),
        "毕业年份": data.get("graduationYear", ""),
        "经验要求": ("不限" if data.get("workYearType", 0) == 0
                     else f"{data.get('workYearType', 0)}年"),
        "投递时间": (lambda b, e:
                     f"{datetime.fromtimestamp(b/1000).strftime('%Y-%m-%d')} 至 "
                     f"{datetime.fromtimestamp(e/1000).strftime('%Y-%m-%d')}"
                     if b and e else
                     f"{datetime.fromtimestamp(b/1000).strftime('%Y-%m-%d')} 起"
                     if b else "不限"
                     )(data.get("deliverBegin", 0), data.get("deliverEnd", 0)),
        "发布时间": (datetime.fromtimestamp(data["createTime"] / 1000)
                    .strftime("%Y-%m-%d %H:%M")
                    if data.get("createTime") else ""),
        "刷新时间": (datetime.fromtimestamp(data["refreshTime"] / 1000)
                    .strftime("%Y-%m-%d %H:%M")
                    if data.get("refreshTime") else ""),
        "岗位职责": infos,
        "岗位要求": requirements,
        "加分项": bonus,
        "公司ID": company.get("companyId", ""),
        "公司名称": company.get("companyName", ""),
        "公司简称": company.get("companyShortName", ""),
        "公司规模": company.get("personScales", ""),
        "融资阶段": company.get("scaleTagName", ""),
        "所属行业": "，".join(company.get("industryTagNameList", [])),
        "公司地址": company.get("address", ""),
        "公司Logo": company.get("picUrl", ""),
        "公司官网": company.get("siteUrl", ""),
        "公司介绍": "",
        "公司福利": "",
        "创始人介绍": "",
        "公司品牌介绍": "",
        "招聘者": boss.get("userAppellation", ""),
    }


# ==================== (1) requests：获取岗位列表 JSON ====================

def fetch_jobs_via_requests(keyword, recruit_type, city="杭州"):
    """
    使用 requests 库直接调用岗位搜索 API。
    返回岗位数据列表。
    """
    all_jobs = []
    page = 1

    while True:
        form_data = {
            "careerJobId": "", "jobCity": city, "page": page,
            "query": keyword, "random": "true", "recommend": "false",
            "recruitType": recruit_type, "salaryType": 2,
            "pageSize": 20, "requestFrom": 1, "order": 0, "pageSource": 5001,
        }

        try:
            resp = requests.post(LIST_API, headers=HEADERS, data=form_data, timeout=15)
            result = resp.json()
        except Exception as e:
            print(f"      [requests] 请求失败: {e}")
            break

        if result.get("code") != 0:
            print(f"      [requests] API 错误: {result.get('msg', '未知')}")
            break

        data = result.get("data", {})
        items = data.get("datas", [])
        total = data.get("totalCount", 0)
        total_page = data.get("totalPage", 0)

        if page == 1:
            print(f"      [requests] 共 {total} 条, {total_page} 页")

        for item in items:
            all_jobs.append(parse_job_item(item.get("data", {}), keyword, ""))

        print(f"      第 {page}/{total_page} 页 → {len(items)} 条, 累计 {len(all_jobs)} 条")

        if page >= total_page:
            break
        page += 1
        time.sleep(0.3)

    return all_jobs


# ==================== (2) Playwright + BeautifulSoup：获取公司介绍 ====================

async def fetch_company_intro_via_playwright(page, company_id, company_name):
    """
    使用 Playwright 导航到公司页面 + BeautifulSoup 解析 HTML，
    获取公司介绍。
    """
    url = f"https://www.nowcoder.com/careers/{company_id}"
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(1)
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        # 尝试多种选择器定位公司介绍
        intro = ""
        for sel in [".company-desc", ".company-intro", ".company-description",
                    ".detail-content", '[class*="company"][class*="desc"]']:
            el = soup.select_one(sel)
            if el and len(el.get_text(strip=True)) > 20:
                intro = el.get_text(strip=True)
                break

        # 正则兜底：提取"公司介绍"后的文本
        if not intro:
            match = re.search(
                r"(?:公司简介|公司介绍|企业简介)[\s\S]*?(?=\n(?:在招职位|招聘岗位|公司福利|$))",
                soup.get_text(separator="\n"),
            )
            if match:
                lines = [l.strip() for l in match.group().split("\n") if l.strip() and len(l.strip()) > 3]
                intro = "\n".join(lines)

        return intro.strip()
    except Exception as e:
        print(f"      [Playwright] 页面导航失败: {e}")
        return ""


# ==================== (3) requests：获取公司详情 JSON ====================

def fetch_company_detail_via_requests(company_id):
    """使用 requests 库获取公司详情 API 的 JSON 数据。"""
    try:
        resp = requests.get(
            f"{COMPANY_API}?companyId={company_id}",
            headers={**HEADERS, "Referer": f"https://www.nowcoder.com/careers/{company_id}"},
            timeout=15,
        )
        data = resp.json()
        if data.get("code") != 0:
            return {}
        c = data.get("data", {}).get("recommendInternCompany", {}) or {}
        return {
            "公司介绍": html_to_text(c.get("detail", "")),
            "公司官网": c.get("siteUrl", ""),
            "公司福利": html_to_text(c.get("companyWelfare", "")),
            "创始人介绍": html_to_text(c.get("originatorIntroduction", "")),
            "公司品牌介绍": html_to_text(c.get("brandIntroduction", "")),
        }
    except Exception as e:
        print(f"      [requests] 公司详情失败: {e}")
        return {}


async def enrich_company_intros(page, jobs):
    """补全所有岗位的公司介绍（requests 优先 → Playwright 兜底）"""
    unique = {j["公司ID"]: j["公司名称"] for j in jobs if j.get("公司ID")}
    if not unique:
        return jobs

    print(f"\n  [公司介绍] 共 {len(unique)} 家, 获取中...")
    cache = {}

    for i, (cid, cname) in enumerate(unique.items(), 1):
        print(f"    [{i}/{len(unique)}] {cname}", end="")

        # 策略一：requests 调 API
        detail = fetch_company_detail_via_requests(cid)
        if detail.get("公司介绍"):
            cache[cid] = detail
            print(f"  (requests API)")
            continue

        # 策略二：Playwright 打开页面 + BeautifulSoup 解析
        intro = await fetch_company_intro_via_playwright(page, cid, cname)
        if intro:
            cache[cid] = {"公司介绍": intro}
            print(f"  (Playwright + BS4)")
        else:
            cache[cid] = {}
            print(f"  (无介绍)")

        await asyncio.sleep(0.3)

    for job in jobs:
        cid = job.get("公司ID", "")
        if cid in cache:
            for k, v in cache[cid].items():
                if k in job and not job[k]:
                    job[k] = v

    return jobs


# ==================== 去重 ====================

def deduplicate(jobs):
    seen = set()
    result = []
    for j in jobs:
        jid = j.get("岗位ID", "")
        if jid and jid not in seen:
            seen.add(jid)
            result.append(j)
    return result


# ==================== (5) JSON 保存 ====================

def save_json(jobs, filepath):
    """保存为 JSON 文件"""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    kb = os.path.getsize(filepath) / 1024
    print(f"  [JSON] {os.path.basename(filepath)} ({kb:.1f} KB, {len(jobs)} 条)")


# ==================== (6) 数据库导入 ====================

def import_to_database():
    """
    将 output/ 下的 JSON 文件导入 SQLite 数据库。
    复用 backend 的数据模型。
    """
    print("\n" + "=" * 70)
    print("  导入数据库...")
    print("=" * 70)

    # 设置路径以导入 backend 模块
    backend_src = os.path.join(BACKEND_DIR, "app")
    if not os.path.isdir(backend_src):
        print("  [数据库] backend/app/ 不存在，跳过导入")
        return
    sys.path.insert(0, BACKEND_DIR)

    try:
        import asyncio as aio
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import Session

        # 使用同步引擎连接数据库
        db_path = os.path.join(BACKEND_DIR, "data", "jobs.db")
        if not os.path.exists(db_path):
            print(f"  [数据库] {db_path} 不存在，创建中...")
        engine = create_engine(f"sqlite:///{db_path}", echo=False)

        # 创建表
        from app.database import Base as AppBase
        from app.models import JobCategory, Company, JobPosition, Skill, JobSkillRel
        AppBase.metadata.create_all(engine)

        session = Session(engine)

        # 获取已有的 origin_id 集合（用于去重）
        existing_ids = set(
            row[0] for row in
            session.execute(text("SELECT origin_id FROM job_position WHERE origin_id IS NOT NULL"))
            if row[0]
        )
        print(f"  [数据库] 已有 {len(existing_ids)} 条岗位记录")

        # 获取分类映射
        cat_map = {c.name: c.id for c in session.query(JobCategory).all()}
        stats = {"created": 0, "skipped": 0, "companies": 0}

        # 遍历所有 JSON 文件
        for fname in sorted(os.listdir(OUTPUT_DIR)):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(OUTPUT_DIR, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                jobs = json.load(f)

            if not jobs:
                continue

            recruit_type = fname.replace("岗位.json", "").replace(".json", "")
            print(f"\n  [{recruit_type}] {len(jobs)} 条待导入")

            for item in jobs:
                origin_id = str(item.get("岗位ID", ""))
                if not origin_id or origin_id in existing_ids:
                    stats["skipped"] += 1
                    continue

                # 公司
                company_id = None
                company_name = item.get("公司名称", "").strip()
                if company_name:
                    company = session.query(Company).filter(Company.name == company_name).first()
                    if not company:
                        company = Company(
                            origin_id=str(item.get("公司ID", "")),
                            name=company_name,
                            short_name=item.get("公司简称", ""),
                            scale=item.get("公司规模", ""),
                            financing_stage=item.get("融资阶段", ""),
                            industry=item.get("所属行业", ""),
                            address=item.get("公司地址", ""),
                            logo_url=item.get("公司Logo", ""),
                            website=item.get("公司官网", ""),
                            description=item.get("公司介绍", ""),
                        )
                        session.add(company)
                        session.flush()
                        stats["companies"] += 1
                    company_id = company.id

                # 岗位分类
                category_id = None
                name = item.get("岗位名称", "")
                for pattern, cat in [
                    (r"后端|Java|Go|Python.*开发|云服务|微服务", "后端开发"),
                    (r"前端|Vue|React|Web前端|H5", "前端开发"),
                    (r"AI|人工智能|算法|机器学习|深度学习|大模型|LLM", "人工智能"),
                    (r"测试|测开|QA|质量保障", "测试开发"),
                    (r"运维|SRE|DevOps", "运维开发"),
                    (r"安全|网络安全|信息安全", "安全"),
                    (r"数据", "数据开发"),
                    (r"产品", "产品类"),
                ]:
                    if re.search(pattern, name, re.IGNORECASE):
                        category_id = cat_map.get(cat)
                        break

                # 时间
                publish_time = None
                try:
                    pt = item.get("发布时间", "")
                    if pt:
                        publish_time = datetime.strptime(pt, "%Y-%m-%d %H:%M")
                except ValueError:
                    pass

                # 创建岗位
                job = JobPosition(
                    origin_id=origin_id,
                    name=name,
                    url=item.get("岗位链接", ""),
                    company_id=company_id,
                    category_id=category_id,
                    city=item.get("工作城市", ""),
                    salary_text=item.get("薪资", ""),
                    salary_type=item.get("薪资类型", ""),
                    salary_min=item.get("薪资下限", 0),
                    salary_max=item.get("薪资上限", 0),
                    education_required=item.get("学历要求", ""),
                    tags=item.get("岗位标签", ""),
                    responsibility=item.get("岗位职责", ""),
                    requirement=item.get("岗位要求", ""),
                    bonus=item.get("加分项", ""),
                    publish_time=publish_time,
                    source="牛客网",
                    recruit_type=recruit_type,
                )
                session.add(job)
                existing_ids.add(origin_id)
                stats["created"] += 1

                if stats["created"] % 20 == 0:
                    session.commit()

            session.commit()

        session.close()
        engine.dispose()

        print(f"\n  [数据库] 导入完成!")
        print(f"    新增岗位: {stats['created']}")
        print(f"    跳过(已存在): {stats['skipped']}")
        print(f"    新增公司: {stats['companies']}")

    except ImportError as e:
        print(f"  [数据库] 导入失败(缺少依赖): {e}")
        print(f"  请先安装: pip install sqlalchemy aiosqlite")
    except Exception as e:
        print(f"  [数据库] 导入出错: {e}")
        import traceback
        traceback.print_exc()


# ==================== 统计 ====================

def print_summary(all_results):
    """打印爬取结果总览"""
    print("\n" + "=" * 70)
    print("  爬取结果总览")
    print("=" * 70)
    total = 0
    for name, jobs in all_results.items():
        companies = len(set(j.get("公司ID", "") for j in jobs if j.get("公司ID")))
        has_intro = sum(1 for j in jobs if j.get("公司介绍", ""))
        print(f"\n  【{name}】{len(jobs)} 条, {companies} 家公司, "
              f"有介绍 {has_intro}/{len(jobs)}")
        # 关键词分布
        kw = {}
        for j in jobs:
            k = j.get("搜索关键词", "未知")
            kw[k] = kw.get(k, 0) + 1
        for k, c in sorted(kw.items(), key=lambda x: x[1], reverse=True):
            print(f"    {k}: {c}")
        total += len(jobs)
    print(f"\n  总计: {total} 个岗位")
    print("=" * 70)


# ==================== 主流程 ====================

async def main():
    print("=" * 70)
    print("  牛客网杭州地区计算机岗位招聘爬虫")
    print(f"  关键词: {len(JOB_KEYWORDS)} 个, 招聘类型: 校招/实习/社招")
    print("=" * 70)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_results = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=HEADERS["User-Agent"],
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
        )
        page = await context.new_page()

        # 先访问首页建立会话
        print("\n[浏览器] 建立会话...")
        await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(1)

        # 遍历三种招聘类型
        for rt in RECRUIT_TYPES:
            name = rt["name"]
            rtype = rt["recruit_type"]
            print(f"\n{'='*70}")
            print(f"  【{name}】开始爬取")
            print(f"{'='*70}")

            all_jobs = []

            for ki, kw in enumerate(JOB_KEYWORDS, 1):
                print(f"\n  [{ki}/{len(JOB_KEYWORDS)}] {kw}")
                try:
                    jobs = fetch_jobs_via_requests(kw, rtype)
                    # 补上招聘类型和关键词
                    for j in jobs:
                        j["招聘类型"] = name
                        j["搜索关键词"] = kw
                    all_jobs.extend(jobs)
                    print(f"  ✅ '{kw}' → {len(jobs)} 条, 累计 {len(all_jobs)} 条")
                except Exception as e:
                    print(f"  ❌ '{kw}' 失败: {e}")

                time.sleep(0.5)

            # 去重
            before = len(all_jobs)
            all_jobs = deduplicate(all_jobs)
            print(f"\n  [去重] {before} → {len(all_jobs)} 条")

            # 补全公司介绍
            all_jobs = await enrich_company_intros(page, all_jobs)

            # 保存 JSON
            save_json(all_jobs, os.path.join(OUTPUT_DIR, f"{name}岗位.json"))
            all_results[name] = all_jobs

        await browser.close()

    print_summary(all_results)
    print(f"\n✅ 爬取完成! JSON 文件保存在: {OUTPUT_DIR}")

    # 导入数据库
    import_to_database()


if __name__ == "__main__":
    asyncio.run(main())
