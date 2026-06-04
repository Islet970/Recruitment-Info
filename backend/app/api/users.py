from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import verify_password, hash_password
from app.models.user import User
from app.models.favorite import UserFavorite
from app.models.position import JobPosition
from app.schemas import PasswordChange, PositionResponse, UserResponse, UserUpdate, PaginatedResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
def update_profile(
    update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if update.username is not None:
        current_user.username = update.username
    if update.email is not None:
        current_user.email = update.email
    if update.avatar_url is not None:
        current_user.avatar_url = update.avatar_url
    db.flush()
    db.refresh(current_user)
    return current_user


@router.put("/me/password")
def change_password(
    pw_change: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(pw_change.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Old password is incorrect")
    current_user.hashed_password = hash_password(pw_change.new_password)
    db.flush()
    return {"message": "Password updated"}


@router.get("/me/favorites")
def list_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count_query = select(func.count()).select_from(
        select(UserFavorite).where(UserFavorite.user_id == current_user.id).subquery()
    )
    total = db.execute(count_query).scalar()

    query = (
        select(UserFavorite)
        .where(UserFavorite.user_id == current_user.id)
        .options(joinedload(UserFavorite.position).joinedload(JobPosition.company))
        .order_by(UserFavorite.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = db.execute(query)
    favs = result.unique().scalars().all()

    items = []
    for fav in favs:
        p = fav.position
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
        ).model_dump())

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("/me/favorites/{position_id}")
def add_favorite(
    position_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = db.execute(select(JobPosition).where(JobPosition.id == position_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Position not found")

    result = db.execute(
        select(UserFavorite).where(
            UserFavorite.user_id == current_user.id,
            UserFavorite.position_id == position_id,
        )
    )
    if result.scalar_one_or_none():
        return {"message": "Already favorited"}

    fav = UserFavorite(user_id=current_user.id, position_id=position_id)
    db.add(fav)
    return {"message": "Added to favorites"}


@router.delete("/me/favorites/{position_id}")
def remove_favorite(
    position_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = db.execute(
        select(UserFavorite).where(
            UserFavorite.user_id == current_user.id,
            UserFavorite.position_id == position_id,
        )
    )
    fav = result.scalar_one_or_none()
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")

    db.delete(fav)
    return {"message": "Removed from favorites"}


@router.delete("/me/account")
def delete_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.delete(current_user)
    return {"message": "Account deleted"}
