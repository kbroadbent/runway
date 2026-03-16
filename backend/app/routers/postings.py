from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import JobPosting, Company
from app.schemas.job_posting import JobPostingCreate, JobPostingUpdate, JobPostingRead

router = APIRouter(prefix="/api/postings", tags=["postings"])


def _get_or_create_company(db: Session, name: str) -> Company:
    company = db.query(Company).filter(Company.name == name).first()
    if not company:
        company = Company(name=name)
        db.add(company)
        db.flush()
    return company


@router.get("", response_model=list[JobPostingRead])
def list_postings(db: Session = Depends(get_db)):
    postings = db.query(JobPosting).options(joinedload(JobPosting.company), joinedload(JobPosting.pipeline_entry)).all()
    results = []
    for p in postings:
        data = JobPostingRead.model_validate(p)
        data.pipeline_stage = p.pipeline_entry.stage if p.pipeline_entry else None
        results.append(data)
    return results


@router.post("", response_model=JobPostingRead, status_code=201)
def create_posting(data: JobPostingCreate, db: Session = Depends(get_db)):
    company_id = data.company_id
    if not company_id and data.company_name:
        company_id = _get_or_create_company(db, data.company_name).id
    posting = JobPosting(
        title=data.title,
        company_id=company_id,
        description=data.description,
        location=data.location,
        remote_type=data.remote_type,
        salary_min=data.salary_min,
        salary_max=data.salary_max,
        url=data.url,
        source=data.source,
    )
    db.add(posting)
    db.commit()
    db.refresh(posting)
    return JobPostingRead.model_validate(posting)


@router.get("/{posting_id}", response_model=JobPostingRead)
def get_posting(posting_id: int, db: Session = Depends(get_db)):
    posting = db.query(JobPosting).options(joinedload(JobPosting.company)).filter(JobPosting.id == posting_id).first()
    if not posting:
        raise HTTPException(status_code=404, detail="Posting not found")
    return posting


@router.put("/{posting_id}", response_model=JobPostingRead)
def update_posting(posting_id: int, data: JobPostingUpdate, db: Session = Depends(get_db)):
    posting = db.get(JobPosting, posting_id)
    if not posting:
        raise HTTPException(status_code=404, detail="Posting not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(posting, key, value)
    db.commit()
    db.refresh(posting)
    return posting


@router.delete("/{posting_id}", status_code=204)
def delete_posting(posting_id: int, db: Session = Depends(get_db)):
    posting = db.get(JobPosting, posting_id)
    if not posting:
        raise HTTPException(status_code=404, detail="Posting not found")
    db.delete(posting)
    db.commit()
    return Response(status_code=204)
