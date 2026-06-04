from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.position import JobPosition, RecruitType
from app.schemas import CompanyBrief, PaginatedResponse, PositionBrief, PositionDetail, PositionResponse

router = APIRouter()


def _build_company_brief(c) -> dict | None:
    if not c:
        return None
    return CompanyBrief(
        id=c.id,
        name=c.name,
        short_name=c.short_name,
        scale=c.scale,
        financing_stage=c.financing_stage,
        industry=c.industry,
        address=c.address,
        logo_url=c.logo_url,
        website=c.website,
        description=c.description,
        benefits=c.benefits,
        position_count=0,
    ).model_dump()


def _build_position_brief(p) -> PositionResponse:
    return PositionResponse(
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
        company=_build_company_brief(p.company),
        category_name=p.category.name if p.category else None,
    )


@router.get("")
def list_positions(
    type: str = Query("campus"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query("", max_length=200),
    category_id: int | None = None,
    city: str = "",
    education: str = "",
    sort_by: str = "publish_time",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    recruit_map = {"campus": RecruitType.CAMPUS, "social": RecruitType.SOCIAL, "intern": RecruitType.INTERN}
    recruit_type = recruit_map.get(type)

    query = (
        select(JobPosition)
        .options(joinedload(JobPosition.company), joinedload(JobPosition.category))
        .where(JobPosition.is_active == True, JobPosition.recruit_type == recruit_type)
    )

    if search:
        query = query.where(JobPosition.name.like(f"%{search}%"))

    if category_id:
        query = query.where(JobPosition.category_id == category_id)

    if city:
        query = query.where(JobPosition.city.like(f"%{city}%"))

    if education:
        query = query.where(JobPosition.education_required.like(f"%{education}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar()

    sort_col = getattr(JobPosition, sort_by, JobPosition.publish_time)
    order_fn = sort_col.desc() if sort_order == "desc" else sort_col.asc()
    query = query.order_by(order_fn)

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = db.execute(query)
    positions = result.unique().scalars().all()

    items = [_build_position_brief(p).model_dump() for p in positions]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{position_id}")
def get_position(
    position_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = db.execute(
        select(JobPosition)
        .options(joinedload(JobPosition.company), joinedload(JobPosition.category))
        .where(JobPosition.id == position_id)
    )
    p = result.unique().scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Position not found")

    skill_result = db.execute(
        text("""
            SELECT s.name FROM position_skills ps
            JOIN skills s ON ps.skill_id = s.id
            WHERE ps.position_id = :pid
        """),
        {"pid": position_id},
    )
    skills = [row[0] for row in skill_result.fetchall()]

    return PositionDetail(
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
        url=p.url,
        responsibility=p.responsibility,
        requirement=p.requirement,
        bonus=p.bonus,
        source=p.source,
        skills=skills,
        company=_build_company_brief(p.company),
        category_name=p.category.name if p.category else None,
    ).model_dump()


@router.get("/{position_id}/similar")
def get_similar_positions(
    position_id: int,
    limit: int = 6,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = db.execute(select(JobPosition).where(JobPosition.id == position_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Position not found")

    query = (
        select(JobPosition)
        .options(joinedload(JobPosition.company))
        .where(
            JobPosition.is_active == True,
            JobPosition.id != position_id,
            or_(
                JobPosition.category_id == p.category_id,
                JobPosition.city == p.city,
            ),
        )
        .limit(limit)
    )
    result = db.execute(query)
    positions = result.unique().scalars().all()

    return [_build_position_brief(p2).model_dump() for p2 in positions]
