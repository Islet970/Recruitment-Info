from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.resume import Resume
from app.models.analysis import ResumeAnalysis, AnalysisStatus
from app.schemas import AnalysisResponse

router = APIRouter()


@router.post("/analyze/{resume_id}")
def trigger_analysis(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == current_user.id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    analysis = ResumeAnalysis(
        resume_id=resume_id,
        user_id=current_user.id,
        status=AnalysisStatus.PROCESSING,
    )
    db.add(analysis)
    db.flush()
    db.refresh(analysis)

    mock_skills = ["Python", "JavaScript", "React", "SQL", "Git"]
    mock_experience = 3.0
    mock_education = "本科"
    mock_directions = ["后端开发", "全栈开发"]

    analysis.analysis_result = {
        "summary": "具有扎实的编程基础和实践经验",
        "strengths": ["编程能力较强", "项目经验丰富"],
        "weaknesses": ["缺乏大型项目经验"],
        "detailed_analysis": "基于简历内容的综合分析结果",
    }
    analysis.extracted_skills = mock_skills
    analysis.experience_years = mock_experience
    analysis.education_level = mock_education
    analysis.recommended_directions = mock_directions
    analysis.status = AnalysisStatus.COMPLETED
    db.flush()
    db.refresh(analysis)

    return {"analysis_id": analysis.id, "status": "completed"}


@router.get("/{analysis_id}")
def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = db.execute(
        select(ResumeAnalysis).where(
            ResumeAnalysis.id == analysis_id,
            ResumeAnalysis.user_id == current_user.id,
        )
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return AnalysisResponse(
        id=analysis.id,
        resume_id=analysis.resume_id,
        status=analysis.status.value,
        analysis_result=analysis.analysis_result,
        extracted_skills=analysis.extracted_skills,
        experience_years=float(analysis.experience_years) if analysis.experience_years else None,
        education_level=analysis.education_level,
        recommended_directions=analysis.recommended_directions,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
    )


@router.get("")
def list_analysis_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count_query = select(func.count()).select_from(
        select(ResumeAnalysis).where(ResumeAnalysis.user_id == current_user.id).subquery()
    )
    total = db.execute(count_query).scalar()

    query = (
        select(ResumeAnalysis)
        .where(ResumeAnalysis.user_id == current_user.id)
        .order_by(ResumeAnalysis.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = db.execute(query)
    analyses = result.scalars().all()

    items = [
        AnalysisResponse(
            id=a.id,
            resume_id=a.resume_id,
            status=a.status.value,
            analysis_result=a.analysis_result,
            extracted_skills=a.extracted_skills,
            experience_years=float(a.experience_years) if a.experience_years else None,
            education_level=a.education_level,
            recommended_directions=a.recommended_directions,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in analyses
    ]

    return {
        "items": [item.model_dump() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.delete("/{analysis_id}")
def delete_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = db.execute(
        select(ResumeAnalysis).where(
            ResumeAnalysis.id == analysis_id,
            ResumeAnalysis.user_id == current_user.id,
        )
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    db.delete(analysis)
    return {"message": "Analysis deleted"}
