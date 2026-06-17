from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.positions import router as positions_router
from app.api.companies import router as companies_router
from app.api.categories import router as categories_router
from app.api.skills import router as skills_router
from app.api.resumes import router as resumes_router
from app.api.analysis import router as analysis_router
from app.api.recommendations import router as recommendations_router
from app.api.users import router as users_router
from app.api.ml import router as ml_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(positions_router, prefix="/positions", tags=["Positions"])
api_router.include_router(companies_router, prefix="/companies", tags=["Companies"])
api_router.include_router(categories_router, prefix="/categories", tags=["Categories"])
api_router.include_router(skills_router, prefix="/skills", tags=["Skills"])
api_router.include_router(resumes_router, prefix="/resumes", tags=["Resumes"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["Analysis"])
api_router.include_router(recommendations_router, prefix="/recommendations", tags=["Recommendations"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(ml_router, prefix="/ml", tags=["Machine Learning"])
