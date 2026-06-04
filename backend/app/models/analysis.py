from datetime import datetime

from sqlalchemy import DateTime, DECIMAL, Enum as SAEnum, ForeignKey, String, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
import enum


class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ResumeAnalysis(Base):
    __tablename__ = "resume_analyses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    extracted_skills: Mapped[list | None] = mapped_column(JSON, nullable=True)
    experience_years: Mapped[float | None] = mapped_column(DECIMAL(4, 1), nullable=True)
    education_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    recommended_directions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    status: Mapped[AnalysisStatus] = mapped_column(
        SAEnum(AnalysisStatus), default=AnalysisStatus.PENDING, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    # Relationships
    resume = relationship("Resume", back_populates="analyses")
    user = relationship("User", back_populates="analyses")
