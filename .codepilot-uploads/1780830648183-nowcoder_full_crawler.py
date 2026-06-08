#!/usr/bin/env python3
"""
牛客网杭州地区计算机岗位招聘信息爬虫
====================================
技术栈覆盖:
  (1) requests       — 直接 HTTP 请求获取岗位列表 JSON + 公司详情 JSON
  (2) Playwright     — 浏览器自动化，打开公司页面获取公司介绍
  (3) BeautifulSoup  — 解析公司页面 HTML
  (4) 正则表达式     — 文本清洗、HTML 标签剥离
  (5) JSON           — 数据保存

爬取: 28 种计算机岗位 × 校招/实习/社招
输出: output/{校招,实习,社招}岗位.json
"""

import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime

import requests
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# ==================== Windows 编码 ====================
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ==================== 配置 ====================
JOB_KEYWORDS = [
    "Java"
]

RECRUIT_TYPES = [
    {"name": "校招", "recruit_type": 1},
    {"name": "实习", "recruit_type": 2},
    {"name": "社招", "recruit_type": 3},
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

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
    if not html_str:
        return ""
    if not isinstance(html_str, str):
        html_str = str(html_str)
    text = re.sub(r"<[^>]+>", "", html_str)
    for entity, char in [("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"),
                         ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'")]:
        text = text.replace(entity, char)
    return re.sub(r"\n\s*\n", "\n", text).strip()


def bs_html_to_text(html_str):
    if not html_str:
        return ""
    return BeautifulSoup(html_str, "html.parser").get_text(separator="\n").strip()

#解析 ext JSON 字段，提取岗位职责、岗位要求、加分项
def parse_ext(ext_str):

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
        "公司网址": f"https://www.nowcoder.com/enterprise/{company.get('companyId', '')}",
        "公司介绍": "",
        "招聘者": boss.get("userAppellation", ""),
    }


# ==================== (1) requests：获取岗位列表 JSON ====================

def fetch_jobs_via_requests(keyword, recruit_type, recruit_name, city="杭州"):
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
            all_jobs.append(parse_job_item(item.get("data", {}), keyword, recruit_name))

        print(f"      第 {page}/{total_page} 页 → {len(items)} 条, 累计 {len(all_jobs)} 条")

        if page >= total_page:
            break
        page += 1
        time.sleep(0.3)

    return all_jobs


# ==================== (2) Playwright + BeautifulSoup：获取公司介绍 & 官网 ====================

async def fetch_company_intro_via_playwright(page, company_id, company_name):

    url = f"https://www.nowcoder.com/enterprise/{company_id}"
    result = ""
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(2)
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        company_info_el = soup.select_one(".company-info")
        if company_info_el:
            text = company_info_el.get_text(separator="\n", strip=True)
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            result = "\n".join(lines)

        if result:
            print(f"通过Playwright获取公司介绍  ")
        else:
            print(f"未找到公司介绍  ")
        return result
    except Exception as e:
        print(f"报错: {e}")
        return ""


# ==================== (3) requests：获取公司详情 JSON ====================

def fetch_company_detail_via_requests(company_id):
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
            "公司介绍": html_to_text(c.get("detail", ""))
        }
    except Exception as e:
        print(f"      [requests] 公司详情失败: {e}")
        return {}

#补全所有岗位的公司信息（requests 优先 → Playwright 兜底）
async def enrich_company_intros(page, jobs):
    unique = {j["公司ID"]: j["公司名称"] for j in jobs if j.get("公司ID")}
    if not unique:
        return jobs

    print(f"\n  [公司信息] 共 {len(unique)} 家, 获取中...")
    cache = {}

    for i, (cid, cname) in enumerate(unique.items(), 1):
        print(f"    [{i}/{len(unique)}] {cname} ...", end="", flush=True)

        # === requests 调 API ===
        detail = fetch_company_detail_via_requests(cid)
        if detail.get("公司介绍"):
            cache[cid] = detail
            print(f" requests ok")
            continue

        # === Playwright 补公司介绍 ===
        intro = await fetch_company_intro_via_playwright(page, cid, cname)
        if intro:
            cache[cid] = {"公司介绍": intro}
            print(f" playwright OK")
        else:
            cache[cid] = {"公司介绍": ""}
            print(f" 无数据")

        await asyncio.sleep(0.3)

    # 将缓存数据写回岗位
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
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    kb = os.path.getsize(filepath) / 1024
    print(f"  [JSON] {os.path.basename(filepath)} ({kb:.1f} KB, {len(jobs)} 条)")


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
                    jobs = fetch_jobs_via_requests(kw, rtype, name)
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


if __name__ == "__main__":
    asyncio.run(main())
