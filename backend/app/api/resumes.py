from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.orm import Session
import os
import uuid

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.resume import Resume
from app.schemas import ResumeResponse

router = APIRouter()


@router.post("/upload")
def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    allowed_types = {".pdf": "pdf", ".docx": "docx", ".doc": "doc"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_types:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    file_id = str(uuid.uuid4())
    saved_name = f"{file_id}{ext}"
    file_path = os.path.join(upload_dir, saved_name)

    content = file.file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    with open(file_path, "wb") as f:
        f.write(content)

    resume = Resume(
        user_id=current_user.id,
        file_name=file.filename,
        file_path=file_path,
        file_type=allowed_types[ext],
    )
    db.add(resume)
    db.flush()
    db.refresh(resume)

    return ResumeResponse(
        id=resume.id, file_name=resume.file_name,
        file_type=resume.file_type, upload_time=resume.upload_time,
    )


@router.get("")
def list_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = db.execute(
        select(Resume).where(Resume.user_id == current_user.id).order_by(Resume.upload_time.desc())
    )
    resumes = result.scalars().all()
    return [
        ResumeResponse(id=r.id, file_name=r.file_name, file_type=r.file_type, upload_time=r.upload_time)
        for r in resumes
    ]


@router.get("/{resume_id}")
def get_resume(
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
    return ResumeResponse(
        id=resume.id, file_name=resume.file_name,
        file_type=resume.file_type, upload_time=resume.upload_time,
    )


@router.delete("/{resume_id}")
def delete_resume(
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

    if os.path.exists(resume.file_path):
        os.remove(resume.file_path)

    db.delete(resume)
    return {"message": "Resume deleted"}
