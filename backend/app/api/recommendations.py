from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.analysis import ResumeAnalysis
from app.models.position import JobPosition
from app.schemas import PositionResponse

router = APIRouter()


@router.get("/career-paths")
def get_career_paths(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = db.execute(
        select(ResumeAnalysis).where(
            ResumeAnalysis.id == analysis_id,
            ResumeAnalysis.user_id == current_user.id,
        )
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    directions = analysis.recommended_directions or []
    skills = analysis.extracted_skills or []

    career_paths = []
    for direction in directions:
        career_paths.append({
            "direction": direction,
            "description": f"基于您的技能和经验，推荐从事{direction}方向",
            "match_score": 85.0,
            "required_skills": skills,
            "suggested_skills": ["系统设计", "分布式架构", "性能优化"],
        })

    return career_paths


@router.get("/positions")
def get_recommended_positions(
    analysis_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = db.execute(
        select(ResumeAnalysis).where(
            ResumeAnalysis.id == analysis_id,
            ResumeAnalysis.user_id == current_user.id,
        )
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    skills = analysis.extracted_skills or []

    if skills:
        like_conditions = " OR ".join([f"jp.name LIKE '%{s}%'" for s in skills])
        query = text(f"""
            SELECT DISTINCT jp.id FROM job_positions jp
            WHERE jp.is_active = 1 AND ({like_conditions})
            LIMIT :limit OFFSET :offset
        """)
        pos_result = db.execute(query, {"limit": page_size, "offset": (page - 1) * page_size})
        pos_ids = [row[0] for row in pos_result.fetchall()]

        if pos_ids:
            pos_query = (
                select(JobPosition)
                .options(joinedload(JobPosition.company))
                .where(JobPosition.id.in_(pos_ids))
            )
            pos_result = db.execute(pos_query)
            positions = pos_result.unique().scalars().all()
        else:
            positions = []
    else:
        positions = []

    return [
        PositionResponse(
            id=p.id,
            name=p.name,
            recruit_type=p.recruit_type.value,
            city=p.city,
            location=p.location,
            salary_text=p.salary_text,
            salary_type=p.salary_type,
            salary_min=float(p.salary_min),
            salary_max=float(p.salary_max),
            education_required=p.education_required,
            experience_required=p.experience_required,
            tags=p.tags,
            publish_time=p.publish_time,
            company={
                "id": p.company.id,
                "name": p.company.name,
                "short_name": p.company.short_name,
                "scale": p.company.scale,
                "financing_stage": p.company.financing_stage,
                "industry": p.company.industry,
                "address": p.company.address,
                "logo_url": p.company.logo_url,
                "website": p.company.website,
                "description": p.company.description,
                "benefits": p.company.benefits,
                "position_count": 0,
            } if p.company else None,
            category_name=p.category.name if hasattr(p, 'category') and p.category else None,
        ).model_dump()
        for p in positions
    ]
