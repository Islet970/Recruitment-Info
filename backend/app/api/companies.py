from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.company import Company
from app.models.position import JobPosition
from app.schemas import CompanyDetail, CompanyResponse, PaginatedResponse, PositionBriefForCompany

router = APIRouter()


@router.get("")
def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    scale: str = "",
    industry: str = "",
    search: str = "",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = select(Company)

    if scale:
        query = query.where(Company.scale == scale)
    if industry:
        query = query.where(Company.industry.like(f"%{industry}%"))
    if search:
        query = query.where(Company.name.like(f"%{search}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar()

    query = query.order_by(Company.name.asc()).offset((page - 1) * page_size).limit(page_size)
    result = db.execute(query)
    companies = result.scalars().all()

    items = []
    for c in companies:
        pos_count = db.execute(
            select(func.count()).select_from(select(JobPosition).where(JobPosition.company_id == c.id).subquery())
        ).scalar()
        items.append(CompanyResponse(
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
            position_count=pos_count,
        ))

    return PaginatedResponse(
        items=[item.model_dump() for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/scales")
def list_scales(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    result = db.execute(
        select(Company.scale).where(Company.scale.isnot(None), Company.scale != "").distinct()
    )
    return [row[0] for row in result.fetchall()]


@router.get("/industries")
def list_industries(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    result = db.execute(
        select(Company.industry)
        .where(Company.industry.isnot(None), Company.industry != "")
        .distinct()
    )
    industries = []
    for row in result.fetchall():
        val = row[0]
        if val:
            for part in val.split("，"):
                part = part.strip()
                if part and part not in industries:
                    industries.append(part)
    return sorted(industries)


@router.get("/{company_id}")
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = db.execute(select(Company).where(Company.id == company_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Company not found")

    positions_result = db.execute(
        select(JobPosition)
        .where(JobPosition.company_id == company_id, JobPosition.is_active == True)
        .order_by(JobPosition.publish_time.desc())
        .limit(50)
    )
    positions = positions_result.scalars().all()

    pos_list = [
        PositionBriefForCompany(
            id=p.id,
            name=p.name,
            recruit_type=p.recruit_type.value if hasattr(p.recruit_type, 'value') else p.recruit_type,
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
        )
        for p in positions
    ]

    return CompanyDetail(
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
        position_count=len(pos_list),
        positions=[p.model_dump() for p in pos_list],
    ).model_dump()
