from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import JobPosting, Company
from app.schemas.job_posting import JobPostingCreate, JobPostingUpdate, JobPostingRead, ImportRequest, ImportPreview
from app.services.parser_service import parse_posting_text, fetch_and_parse_url

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


@router.post("/import", response_model=ImportPreview)
def import_preview(data: ImportRequest):
    if data.url:
        return fetch_and_parse_url(data.url)
    if data.text:
        return parse_posting_text(data.text)
    raise HTTPException(status_code=400, detail="Provide text or url")


@router.post("/import/confirm", response_model=JobPostingRead, status_code=201)
def import_confirm(data: ImportPreview, db: Session = Depends(get_db)):
    company = None
    if data.company_name:
        company = _get_or_create_company(db, data.company_name)
    posting = JobPosting(
        title=data.title or "Untitled",
        company_id=company.id if company else None,
        description=data.description,
        location=data.location,
        remote_type=data.remote_type,
        salary_min=data.salary_min,
        salary_max=data.salary_max,
        url=data.url,
        source="url_import" if data.url else "pasted",
        raw_content=data.raw_content,
    )
    db.add(posting)
    db.commit()
    db.refresh(posting)
    return posting


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
