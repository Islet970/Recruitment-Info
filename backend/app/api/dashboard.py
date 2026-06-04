from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas import (
    BoxPlotData,
    CategoryDistribution,
    DashboardSummary,
    EducationDistribution,
    SalaryBucket,
    ScaleDistribution,
    SkillCount,
    TrendPoint,
)

router = APIRouter()


def _recruit_filter(type_param: str, prefix: str = "jp.") -> str:
    if type_param == "campus":
        return f"AND {prefix}recruit_type = '校招'"
    elif type_param == "social":
        return f"AND {prefix}recruit_type = '社招'"
    elif type_param == "intern":
        return f"AND {prefix}recruit_type = '实习'"
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
    return [TrendPoint(date=row[0], count=row[1]) for row in result.fetchall()]


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
    return [ScaleDistribution(scale=row[0], count=row[1]) for row in result.fetchall()]


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


@router.get("/salary-distribution")
def get_salary_distribution(
    type: str = "all",
    period: str = "monthly",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rf = _recruit_filter(type)
    query = text(f"""
        SELECT
            FLOOR(
                CASE
                    WHEN jp.salary_type = '日薪' AND :period = 'monthly' THEN (jp.salary_min + jp.salary_max) / 2 * 22 / 1000
                    WHEN :period = 'daily' AND jp.salary_type = '日薪' THEN (jp.salary_min + jp.salary_max) / 2
                    ELSE (jp.salary_min + jp.salary_max) / 2
                END
            ) * 5 as bucket,
            COUNT(*) as cnt
        FROM job_positions jp
        WHERE jp.is_active = 1
          AND jp.salary_min > 0
          AND jp.salary_text NOT LIKE '%面议%'
          {rf}
        GROUP BY bucket
        ORDER BY bucket ASC
    """)
    result = db.execute(query, {"period": period})
    return [SalaryBucket(range=f"{row[0]}-{row[0]+5}", count=row[1]) for row in result.fetchall()]


@router.get("/salary-by-category")
def get_salary_by_category(
    type: str = "all",
    period: str = "monthly",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rf = _recruit_filter(type)
    query = text(f"""
        SELECT
            jc.name,
            MIN(jp.salary_min) as min_sal,
            MAX(jp.salary_max) as max_sal,
            AVG((jp.salary_min + jp.salary_max) / 2) as mean_sal
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
    query = text(f"""
        SELECT
            CASE
                WHEN jp.education_required LIKE '%博士%' THEN '博士'
                WHEN jp.education_required LIKE '%硕士%' THEN '硕士'
                WHEN jp.education_required LIKE '%本科%' THEN '本科'
                WHEN jp.education_required LIKE '%大专%' THEN '大专'
                ELSE '不限'
            END as edu_level,
            MIN(jp.salary_min) as min_sal,
            MAX(jp.salary_max) as max_sal,
            AVG((jp.salary_min + jp.salary_max) / 2) as mean_sal
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
    query = text(f"""
        SELECT
            CASE
                WHEN jp.experience_required LIKE '%10年%' THEN '10年经验'
                WHEN jp.experience_required LIKE '%5年%' OR jp.experience_required LIKE '%3-5年%' THEN '5年经验'
                WHEN jp.experience_required LIKE '%3年%' OR jp.experience_required LIKE '%1-3年%' THEN '3年经验'
                WHEN jp.experience_required LIKE '%1年%' OR jp.experience_required = '经验不限' THEN '1年经验'
                ELSE '不限'
            END as exp_level,
            MIN(jp.salary_min) as min_sal,
            MAX(jp.salary_max) as max_sal,
            AVG((jp.salary_min + jp.salary_max) / 2) as mean_sal
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
    limit: int = 10,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rf = _recruit_filter(type)

    if group_by == "skill":
        query = text(f"""
            SELECT s.name as group_name, MAX((jp.salary_min + jp.salary_max) / 2) as max_sal
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
            SELECT jc.name as group_name, MAX((jp.salary_min + jp.salary_max) / 2) as max_sal
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
