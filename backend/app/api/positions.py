from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.position import JobPosition, RecruitType
from app.schemas import PaginatedResponse, PositionDetail, PositionResponse

router = APIRouter()


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

    items = []
    for p in positions:
        items.append(PositionResponse(
            id=p.id,
            name=p.name,
            recruit_type=p.recruit_type.value,
            city=p.city,
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
                "industry": p.company.industry,
                "logo_url": p.company.logo_url,
            } if p.company else None,
            category_name=p.category.name if p.category else None,
        ))

    return PaginatedResponse(
        items=[item.model_dump() for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{position_id}", response_model=PositionDetail)
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
        company={
            "id": p.company.id,
            "name": p.company.name,
            "short_name": p.company.short_name,
            "scale": p.company.scale,
            "industry": p.company.industry,
            "logo_url": p.company.logo_url,
        } if p.company else None,
        category_name=p.category.name if p.category else None,
    )


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

    return [
        PositionResponse(
            id=p2.id,
            name=p2.name,
            recruit_type=p2.recruit_type.value,
            city=p2.city,
            salary_text=p2.salary_text,
            salary_type=p2.salary_type,
            salary_min=float(p2.salary_min),
            salary_max=float(p2.salary_max),
            education_required=p2.education_required,
            experience_required=p2.experience_required,
            tags=p2.tags,
            publish_time=p2.publish_time,
            company={
                "id": p2.company.id,
                "name": p2.company.name,
                "short_name": p2.company.short_name,
                "scale": p2.company.scale,
                "industry": p2.company.industry,
                "logo_url": p2.company.logo_url,
            } if p2.company else None,
        ).model_dump()
        for p2 in positions
    ]
