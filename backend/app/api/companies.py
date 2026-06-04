from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.company import Company
from app.models.position import JobPosition
from app.schemas import CompanyResponse, PaginatedResponse

router = APIRouter()


@router.get("")
def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    scale: str = "",
    search: str = "",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = select(Company)

    if scale:
        query = query.where(Company.scale == scale)
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

    pos_count = db.execute(
        select(func.count()).select_from(select(JobPosition).where(JobPosition.company_id == company_id).subquery())
    ).scalar()

    return CompanyResponse(
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
    ).model_dump()
