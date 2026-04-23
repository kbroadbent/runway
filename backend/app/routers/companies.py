from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import Company
from app.models.job_posting import JobPosting
from app.models.pipeline import PipelineEntry, InterviewNote
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyRead, CompanyInterviewRead
from app.services.research_service import research_company

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("", response_model=list[CompanyRead])
def list_companies(db: Session = Depends(get_db)):
    return db.query(Company).all()


@router.post("", response_model=CompanyRead, status_code=201)
def create_company(data: CompanyCreate, db: Session = Depends(get_db)):
    company = Company(**data.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.put("/{company_id}", response_model=CompanyRead)
def update_company(company_id: int, data: CompanyUpdate, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(company, key, value)
    db.commit()
    db.refresh(company)
    return company


@router.post("/{company_id}/research", response_model=CompanyRead)
def research_company_endpoint(company_id: int, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return research_company(company, db)


@router.get("/{company_id}/interviews", response_model=list[CompanyInterviewRead])
def get_company_interviews(company_id: int, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    notes = (
        db.query(InterviewNote)
        .join(InterviewNote.pipeline_entry)
        .join(PipelineEntry.job_posting)
        .filter(JobPosting.company_id == company_id)
        .options(
            joinedload(InterviewNote.pipeline_entry).joinedload(PipelineEntry.job_posting)
        )
        .order_by(InterviewNote.scheduled_at.desc())
        .all()
    )

    return [
        CompanyInterviewRead(
            id=n.id,
            round=n.round,
            scheduled_at=n.scheduled_at,
            interviewers=n.interviewers,
            notes=n.notes,
            created_at=n.created_at,
            posting_id=n.pipeline_entry.job_posting.id,
            posting_title=n.pipeline_entry.job_posting.title,
        )
        for n in notes
    ]
