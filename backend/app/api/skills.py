from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.skill import Skill

router = APIRouter()


@router.get("")
def list_skills(
    search: str = "",
    category_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = select(Skill)
    if search:
        query = query.where(Skill.name.like(f"%{search}%"))
    if category_id:
        query = query.where(Skill.category_id == category_id)
    query = query.order_by(Skill.name)
    result = db.execute(query)
    skills = result.scalars().all()
    return [{"id": s.id, "name": s.name, "category_id": s.category_id} for s in skills]
