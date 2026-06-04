from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.category import JobCategory

router = APIRouter()


@router.get("")
def list_categories(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = db.execute(select(JobCategory).order_by(JobCategory.sort_order, JobCategory.name))
    categories = result.scalars().all()
    return [{"id": c.id, "name": c.name} for c in categories]
