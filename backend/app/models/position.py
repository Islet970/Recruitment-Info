from datetime import datetime

from sqlalchemy import DateTime, String, Text, ForeignKey, Enum as SAEnum, DECIMAL, Integer, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
import enum


class RecruitType(str, enum.Enum):
    CAMPUS = "校招"
    SOCIAL = "社招"
    INTERN = "实习"


class JobPosition(Base):
    __tablename__ = "job_positions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    origin_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("job_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    recruit_type: Mapped[RecruitType] = mapped_column(SAEnum(RecruitType), nullable=False, index=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    salary_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    salary_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    salary_min: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0)
    salary_max: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0)
    salary_month: Mapped[int] = mapped_column(Integer, default=0)
    education_required: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    graduation_year: Mapped[str | None] = mapped_column(String(20), nullable=True)
    experience_required: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    tags: Mapped[str | None] = mapped_column(String(500), nullable=True)
    responsibility: Mapped[str | None] = mapped_column(Text, nullable=True)
    requirement: Mapped[str | None] = mapped_column(Text, nullable=True)
    bonus: Mapped[str | None] = mapped_column(Text, nullable=True)
    publish_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    refresh_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="牛客网")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    # Relationships
    company = relationship("Company", back_populates="positions")
    category = relationship("JobCategory", back_populates="positions")
    skill_links = relationship("PositionSkill", back_populates="position", cascade="all, delete-orphan")
    favorites = relationship("UserFavorite", back_populates="position", cascade="all, delete-orphan")


class PositionSkill(Base):
    __tablename__ = "position_skills"

    position_id: Mapped[int] = mapped_column(ForeignKey("job_positions.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)

    position = relationship("JobPosition", back_populates="skill_links")
    skill = relationship("Skill", back_populates="position_links")
