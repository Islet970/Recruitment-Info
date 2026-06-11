from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr


# --- Auth ---
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# --- User ---
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    avatar_url: str | None = None
    is_active: bool = True
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    avatar_url: str | None = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


# --- Company ---
class CompanyBrief(BaseModel):
    id: int
    name: str
    short_name: str | None = None
    scale: str | None = None
    financing_stage: str | None = None
    industry: str | None = None
    address: str | None = None
    logo_url: str | None = None
    website: str | None = None
    description: str | None = None
    benefits: str | None = None
    position_count: int = 0

    class Config:
        from_attributes = True


class CompanyResponse(CompanyBrief):
    pass


class PositionBriefForCompany(BaseModel):
    id: int
    name: str
    recruit_type: str
    city: str | None = None
    location: str | None = None
    salary_text: str | None = None
    salary_type: str | None = None
    salary_min: float = 0
    salary_max: float = 0
    education_required: str | None = None
    experience_required: str | None = None
    tags: str | None = None
    publish_time: datetime | None = None

    class Config:
        from_attributes = True


class CompanyDetail(CompanyBrief):
    positions: list[PositionBriefForCompany] = []


# --- Position ---
class PositionBrief(BaseModel):
    id: int
    name: str
    recruit_type: str
    city: str | None = None
    location: str | None = None
    salary_text: str | None = None
    salary_type: str | None = None
    salary_min: float = 0
    salary_max: float = 0
    education_required: str | None = None
    experience_required: str | None = None
    tags: str | None = None
    publish_time: datetime | None = None
    company: CompanyBrief | None = None
    category_name: str | None = None

    class Config:
        from_attributes = True


class PositionDetail(PositionBrief):
    url: str | None = None
    responsibility: str | None = None
    requirement: str | None = None
    bonus: str | None = None
    source: str | None = None
    skills: list[str] = []

    class Config:
        from_attributes = True


class PositionResponse(PositionBrief):
    pass


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# --- Dashboard ---
class DashboardSummary(BaseModel):
    total_positions: int
    total_companies: int
    total_skills: int


class SkillCount(BaseModel):
    name: str
    count: int


class TrendPoint(BaseModel):
    date: str
    count: int


class CategoryDistribution(BaseModel):
    name: str
    value: int


class ScaleDistribution(BaseModel):
    scale: str
    count: int


class EducationDistribution(BaseModel):
    education: str
    count: int


class SalaryBucket(BaseModel):
    range: str
    count: int


class BoxPlotData(BaseModel):
    name: str
    min: float
    q1: float
    median: float
    q3: float
    max: float
    mean: float


class TopPayingPosition(BaseModel):
    id: int
    name: str
    company_name: str
    salary_text: str | None = None
    salary_avg: float
    category_name: str | None = None


class IndustryDistribution(BaseModel):
    name: str
    value: int


class CompanyPositionCount(BaseModel):
    name: str
    count: int


class FinancingStage(BaseModel):
    stage: str
    count: int


class CityDistribution(BaseModel):
    city: str
    count: int


# --- Resume ---
class ResumeResponse(BaseModel):
    id: int
    file_name: str
    file_type: str | None = None
    upload_time: datetime | None = None

    class Config:
        from_attributes = True


# --- Analysis ---
class AnalysisResponse(BaseModel):
    id: int
    resume_id: int
    status: str
    analysis_result: dict | None = None
    extracted_skills: list[str] | None = None
    experience_years: float | None = None
    education_level: str | None = None
    recommended_directions: list[str] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


# --- Recommendation ---
class CareerPath(BaseModel):
    direction: str
    description: str
    match_score: float
    required_skills: list[str]
    suggested_skills: list[str]


class RecommendedPosition(BaseModel):
    position: PositionBrief
    match_score: float
    match_reasons: list[str]
