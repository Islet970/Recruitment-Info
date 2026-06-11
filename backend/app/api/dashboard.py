from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas import (
    BoxPlotData,
    CategoryDistribution,
    CityDistribution,
    CompanyPositionCount,
    DashboardSummary,
    EducationDistribution,
    FinancingStage,
    IndustryDistribution,
    SalaryBucket,
    ScaleDistribution,
    SkillCount,
    TrendPoint,
)

router = APIRouter()


def _recruit_filter(type_param: str, prefix: str = "jp.") -> str:
    if type_param == "campus":
        return f"AND {prefix}recruit_type = 'CAMPUS'"
    elif type_param == "social":
        return f"AND {prefix}recruit_type = 'SOCIAL'"
    elif type_param == "intern":
        return f"AND {prefix}recruit_type = 'INTERN'"
    return ""


@router.get("/summary", response_model=DashboardSummary)
def get_summary(
    type: str = "all",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rf = _recruit_filter(type)
    where = f"WHERE jp.is_active = 1 {rf}"

    pos_result = db.execute(text(f"SELECT COUNT(*) FROM job_positions jp {where}"))
    total_positions = pos_result.scalar() or 0

    comp_result = db.execute(text(f"SELECT COUNT(DISTINCT jp.company_id) FROM job_positions jp {where}"))
    total_companies = comp_result.scalar() or 0

    skill_result = db.execute(text(f"""
        SELECT COUNT(DISTINCT ps.skill_id)
        FROM position_skills ps
        JOIN job_positions jp ON ps.position_id = jp.id
        WHERE jp.is_active = 1 {_recruit_filter(type)}
    """))
    total_skills = skill_result.scalar() or 0

    return DashboardSummary(
        total_positions=total_positions,
        total_companies=total_companies,
        total_skills=total_skills,
    )


@router.get("/skill-counts")
def get_skill_counts(
    type: str = "all",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rf = _recruit_filter(type)
    query = text(f"""
        SELECT s.name, COUNT(*) as cnt
        FROM position_skills ps
        JOIN skills s ON ps.skill_id = s.id
        JOIN job_positions jp ON ps.position_id = jp.id
        WHERE jp.is_active = 1 {rf}
        GROUP BY s.id, s.name
        ORDER BY cnt DESC
    """)
    result = db.execute(query)
    return [SkillCount(name=row[0], count=row[1]) for row in result.fetchall()]


@router.get("/trends")
def get_trends(
    type: str = "all",
    granularity: str = "month",
    nodes: int = 14,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rf = _recruit_filter(type)
    date_format = "%Y-%m" if granularity == "month" else "%Y-%u"
    query = text(f"""
        SELECT DATE_FORMAT(jp.publish_time, '{date_format}') as period, COUNT(*) as cnt
        FROM job_positions jp
        WHERE jp.is_active = 1 AND jp.publish_time IS NOT NULL {rf}
        GROUP BY period
        ORDER BY period ASC
    """)
    result = db.execute(query)
    all_rows = [{"date": row[0], "count": row[1]} for row in result.fetchall()]

    if not all_rows:
        return [TrendPoint(date="", count=0)]

    # Return all monthly data — frontend will sample for x-axis labels
    # but tooltip shows the full month detail
    return [TrendPoint(date=r["date"], count=r["count"]) for r in all_rows]


@router.get("/category-distribution")
def get_category_distribution(
    type: str = "all",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rf = _recruit_filter(type)
    query = text(f"""
        SELECT jc.name, COUNT(*) as cnt
        FROM job_positions jp
        JOIN job_categories jc ON jp.category_id = jc.id
        WHERE jp.is_active = 1 {rf}
        GROUP BY jc.id, jc.name
        ORDER BY cnt DESC
    """)
    result = db.execute(query)
    return [CategoryDistribution(name=row[0], value=row[1]) for row in result.fetchall()]


@router.get("/company-scale")
def get_company_scale(
    type: str = "all",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rf = _recruit_filter(type)
    query = text(f"""
        SELECT c.scale, COUNT(*) as cnt
        FROM job_positions jp
        JOIN companies c ON jp.company_id = c.id
        WHERE jp.is_active = 1 AND c.scale IS NOT NULL AND c.scale != '' {rf}
        GROUP BY c.scale
        ORDER BY cnt DESC
    """)
    result = db.execute(query)
    rows = result.fetchall()

    # Map raw scale strings to fixed bucket labels
    bucket_map = {
        "0-20": "0-20",
        "20-99": "20-99",
        "100-499": "100-499",
        "500-999": "500-999",
        "1000-9999": "1k-9999",
        "10000-": "1w~",
    }
    bucket_order = ["0-20", "20-99", "100-499", "500-999", "1k-9999", "1w~"]
    buckets = {b: 0 for b in bucket_order}

    for scale, cnt in rows:
        if not scale:
            continue
        raw = scale.strip()
        # Normalize: remove "人" suffix, trim spaces, replace common patterns
        norm = raw.replace("人", "").replace(" ", "").replace(",", "")
        # Try exact match first
        found = False
        for key in bucket_map:
            if norm == key:
                buckets[bucket_map[key]] += cnt
                found = True
                break
        if found:
            continue
        # Range matching
        import re
        nums = re.findall(r'\d+', norm)
        if len(nums) == 2:
            low, high = int(nums[0]), int(nums[1])
            if low < 20:
                buckets["0-20"] += cnt
            elif low < 100:
                buckets["20-99"] += cnt
            elif low < 500:
                buckets["100-499"] += cnt
            elif low < 1000:
                buckets["500-999"] += cnt
            else:
                buckets["1k-9999"] += cnt
        elif len(nums) == 1:
            if int(nums[0]) >= 10000:
                buckets["1w~"] += cnt
            else:
                buckets["1k-9999"] += cnt
        else:
            buckets["1k-9999"] += cnt

    result_list = []
    for b in bucket_order:
        if buckets[b] > 0:
            result_list.append(ScaleDistribution(scale=b, count=buckets[b]))
    return result_list


@router.get("/industry-distribution")
def get_industry_distribution(
    type: str = "all",
    limit: int = 12,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rf = _recruit_filter(type)
    query = text(f"""
        SELECT c.industry, COUNT(*) as cnt
        FROM job_positions jp
        JOIN companies c ON jp.company_id = c.id
        WHERE jp.is_active = 1 AND c.industry IS NOT NULL AND c.industry != '' {rf}
        GROUP BY c.industry
        ORDER BY cnt DESC
        LIMIT {limit}
    """)
    result = db.execute(query)
    return [IndustryDistribution(name=row[0], value=row[1]) for row in result.fetchall()]


@router.get("/company-position-counts")
def get_company_position_counts(
    type: str = "all",
    limit: int = 15,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rf = _recruit_filter(type)
    query = text(f"""
        SELECT c.name, COUNT(*) as cnt
        FROM job_positions jp
        JOIN companies c ON jp.company_id = c.id
        WHERE jp.is_active = 1 {rf}
        GROUP BY c.id, c.name
        ORDER BY cnt DESC
        LIMIT {limit}
    """)
    result = db.execute(query)
    return [CompanyPositionCount(name=row[0], count=row[1]) for row in result.fetchall()]


@router.get("/financing-stage")
def get_financing_stage(
    type: str = "all",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rf = _recruit_filter(type)
    query = text(f"""
        SELECT c.financing_stage, COUNT(*) as cnt
        FROM job_positions jp
        JOIN companies c ON jp.company_id = c.id
        WHERE jp.is_active = 1 AND c.financing_stage IS NOT NULL AND c.financing_stage != '' {rf}
        GROUP BY c.financing_stage
        ORDER BY cnt DESC
    """)
    result = db.execute(query)
    return [FinancingStage(stage=row[0], count=row[1]) for row in result.fetchall()]


@router.get("/city-distribution")
def get_city_distribution(
    type: str = "all",
    limit: int = 15,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rf = _recruit_filter(type)
    query = text(f"""
        SELECT jp.city, COUNT(*) as cnt
        FROM job_positions jp
        WHERE jp.is_active = 1 AND jp.city IS NOT NULL AND jp.city != '' {rf}
        GROUP BY jp.city
        ORDER BY cnt DESC
        LIMIT {limit}
    """)
    result = db.execute(query)
    return [CityDistribution(city=row[0], count=row[1]) for row in result.fetchall()]


@router.get("/education-requirements")
def get_education_requirements(
    type: str = "all",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rf = _recruit_filter(type)
    query = text(f"""
        SELECT
            CASE
                WHEN jp.education_required LIKE '%博士%' THEN '博士'
                WHEN jp.education_required LIKE '%硕士%' THEN '硕士'
                WHEN jp.education_required LIKE '%本科%' THEN '本科'
                WHEN jp.education_required LIKE '%大专%' THEN '大专'
                ELSE '不限'
            END as edu_level,
            COUNT(*) as cnt
        FROM job_positions jp
        WHERE jp.is_active = 1 {rf}
        GROUP BY edu_level
        ORDER BY FIELD(edu_level, '博士', '硕士', '本科', '大专', '不限')
    """)
    result = db.execute(query)
    return [EducationDistribution(education=row[0], count=row[1]) for row in result.fetchall()]


@router.get("/skills-cloud")
def get_skills_cloud(
    type: str = "all",
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rf = _recruit_filter(type)
    query = text(f"""
        SELECT s.name, COUNT(*) as cnt
        FROM position_skills ps
        JOIN skills s ON ps.skill_id = s.id
        JOIN job_positions jp ON ps.position_id = jp.id
        WHERE jp.is_active = 1 {rf}
        GROUP BY s.id, s.name
        ORDER BY cnt DESC
        LIMIT {limit}
    """)
    result = db.execute(query)
    return [SkillCount(name=row[0], count=row[1]) for row in result.fetchall()]


def _salary_value_sql(salary_col: str, period: str) -> str:
    """Generate SQL expression to convert a salary column to the target unit.

    - period='monthly': all values → k/月 (月薪/1000, 日薪*22/1000)
    - period='daily':   all values → 元/日 (日薪 as-is, 月薪/22)
    """
    if period == "monthly":
        return f"""
            CASE
                WHEN jp.salary_type = '日薪' THEN {salary_col} * 22 / 1000
                ELSE {salary_col} / 1000
            END
        """
    else:
        return f"""
            CASE
                WHEN jp.salary_type = '日薪' THEN {salary_col}
                ELSE {salary_col} / 22
            END
        """


@router.get("/salary-distribution")
def get_salary_distribution(
    type: str = "all",
    period: str = "monthly",
    field: str = "min",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if field not in ("min", "max"):
        field = "min"
    rf = _recruit_filter(type)
    salary_col = f"jp.salary_{field}"
    effective = _salary_value_sql(salary_col, period)

    if period == "monthly":
        bucket_size = 5
        range_suffix = "k"
    else:
        bucket_size = 50
        range_suffix = "元/日"

    query = text(f"""
        SELECT
            FLOOR(({effective}) / :bucket_size) * :bucket_size as bucket,
            COUNT(*) as cnt
        FROM job_positions jp
        WHERE jp.is_active = 1
          AND jp.salary_min > 0
          AND jp.salary_text NOT LIKE '%面议%'
          {rf}
        GROUP BY bucket
        ORDER BY bucket ASC
    """)
    result = db.execute(query, {"bucket_size": bucket_size})
    rows = result.fetchall()
    return [SalaryBucket(range=f"{int(row[0])}-{int(row[0]) + bucket_size}{range_suffix}", count=row[1]) for row in rows]


@router.get("/salary-by-category")
def get_salary_by_category(
    type: str = "all",
    period: str = "monthly",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rf = _recruit_filter(type)
    eff_min = _salary_value_sql("jp.salary_min", period)
    eff_max = _salary_value_sql("jp.salary_max", period)
    eff_avg = _salary_value_sql("(jp.salary_min + jp.salary_max) / 2", period)
    query = text(f"""
        SELECT
            jc.name,
            MIN({eff_min}) as min_sal,
            MAX({eff_max}) as max_sal,
            AVG({eff_avg}) as mean_sal
        FROM job_positions jp
        JOIN job_categories jc ON jp.category_id = jc.id
        WHERE jp.is_active = 1
          AND jp.salary_min > 0
          AND jp.salary_text NOT LIKE '%面议%'
          {rf}
        GROUP BY jc.id, jc.name
        HAVING COUNT(*) >= 3
        ORDER BY mean_sal DESC
    """)
    result = db.execute(query)
    return [BoxPlotData(name=row[0], min=float(row[1]), q1=float(row[1]), median=float(row[3]), q3=float(row[2]), max=float(row[2]), mean=float(row[3])) for row in result.fetchall()]


@router.get("/education-vs-salary")
def get_education_vs_salary(
    type: str = "all",
    period: str = "monthly",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rf = _recruit_filter(type)
    eff_min = _salary_value_sql("jp.salary_min", period)
    eff_max = _salary_value_sql("jp.salary_max", period)
    eff_avg = _salary_value_sql("(jp.salary_min + jp.salary_max) / 2", period)
    query = text(f"""
        SELECT
            CASE
                WHEN jp.education_required LIKE '%博士%' THEN '博士'
                WHEN jp.education_required LIKE '%硕士%' THEN '硕士'
                WHEN jp.education_required LIKE '%本科%' THEN '本科'
                WHEN jp.education_required LIKE '%大专%' THEN '大专'
                ELSE '不限'
            END as edu_level,
            MIN({eff_min}) as min_sal,
            MAX({eff_max}) as max_sal,
            AVG({eff_avg}) as mean_sal
        FROM job_positions jp
        WHERE jp.is_active = 1
          AND jp.salary_min > 0
          AND jp.salary_text NOT LIKE '%面议%'
          {rf}
        GROUP BY edu_level
        ORDER BY FIELD(edu_level, '博士', '硕士', '本科', '大专', '不限')
    """)
    result = db.execute(query)
    return [BoxPlotData(name=row[0], min=float(row[1]), q1=float(row[1]), median=float(row[3]), q3=float(row[2]), max=float(row[2]), mean=float(row[3])) for row in result.fetchall()]


@router.get("/experience-vs-salary")
def get_experience_vs_salary(
    type: str = "all",
    period: str = "monthly",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rf = _recruit_filter(type)
    eff_min = _salary_value_sql("jp.salary_min", period)
    eff_max = _salary_value_sql("jp.salary_max", period)
    eff_avg = _salary_value_sql("(jp.salary_min + jp.salary_max) / 2", period)
    query = text(f"""
        SELECT
            CASE
                WHEN jp.experience_required LIKE '%10年%' THEN '10年经验'
                WHEN jp.experience_required LIKE '%5年%' OR jp.experience_required LIKE '%3-5年%' THEN '5年经验'
                WHEN jp.experience_required LIKE '%3年%' OR jp.experience_required LIKE '%1-3年%' THEN '3年经验'
                WHEN jp.experience_required LIKE '%1年%' OR jp.experience_required = '经验不限' THEN '1年经验'
                ELSE '不限'
            END as exp_level,
            MIN({eff_min}) as min_sal,
            MAX({eff_max}) as max_sal,
            AVG({eff_avg}) as mean_sal
        FROM job_positions jp
        WHERE jp.is_active = 1
          AND jp.salary_min > 0
          AND jp.salary_text NOT LIKE '%面议%'
          {rf}
        GROUP BY exp_level
        ORDER BY FIELD(exp_level, '10年经验', '5年经验', '3年经验', '1年经验', '不限')
    """)
    result = db.execute(query)
    return [BoxPlotData(name=row[0], min=float(row[1]), q1=float(row[1]), median=float(row[3]), q3=float(row[2]), max=float(row[2]), mean=float(row[3])) for row in result.fetchall()]


@router.get("/top-paying")
def get_top_paying(
    type: str = "all",
    group_by: str = "category",
    period: str = "monthly",
    limit: int = 10,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rf = _recruit_filter(type)
    eff_avg = _salary_value_sql("(jp.salary_min + jp.salary_max) / 2", period)

    if group_by == "skill":
        query = text(f"""
            SELECT s.name as group_name, MAX({eff_avg}) as max_sal
            FROM job_positions jp
            JOIN position_skills ps ON jp.id = ps.position_id
            JOIN skills s ON ps.skill_id = s.id
            WHERE jp.is_active = 1
              AND jp.salary_min > 0
              AND jp.salary_text NOT LIKE '%面议%'
              {rf}
            GROUP BY s.name
            ORDER BY max_sal DESC
            LIMIT {limit}
        """)
    else:
        query = text(f"""
            SELECT jc.name as group_name, MAX({eff_avg}) as max_sal
            FROM job_positions jp
            JOIN job_categories jc ON jp.category_id = jc.id
            WHERE jp.is_active = 1
              AND jp.salary_min > 0
              AND jp.salary_text NOT LIKE '%面议%'
              {rf}
            GROUP BY jc.name
            ORDER BY max_sal DESC
            LIMIT {limit}
        """)

    result = db.execute(query)
    return [{"name": row[0], "salary_avg": float(row[1])} for row in result.fetchall()]
