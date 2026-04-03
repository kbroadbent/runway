from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models import JobPosting, Company, PipelineEntry, PipelineHistory
from app.schemas.job_posting import JobPostingCreate, JobPostingUpdate, JobPostingRead, ImportRequest, ImportPreview
from app.services.parser_service import parse_posting_text, fetch_and_parse_url
from app.services.ai_service import summarize_posting, AIServiceError

router = APIRouter(prefix="/api/postings", tags=["postings"])


@router.get("", response_model=list[JobPostingRead])
def list_postings(status: str = Query(default='saved'), db: Session = Depends(get_db)):
    query = db.query(JobPosting).options(joinedload(JobPosting.company), joinedload(JobPosting.pipeline_entry))
    if status != 'all':
        query = query.filter(JobPosting.status == status)
    results = []
    for p in query.all():
        data = JobPostingRead.model_validate(p)
        data.pipeline_stage = p.pipeline_entry.stage if p.pipeline_entry else None
        results.append(data)
    return results


@router.post("", response_model=JobPostingRead, status_code=201)
def create_posting(data: JobPostingCreate, db: Session = Depends(get_db)):
    posting = JobPosting(
        title=data.title,
        company_id=data.company_id,
        company_name=data.company_name if not data.company_id else None,
        description=data.description,
        location=data.location,
        remote_type=data.remote_type,
        salary_min=data.salary_min,
        salary_max=data.salary_max,
        url=data.url,
        source=data.source,
        lead_source=data.lead_source,
    )
    db.add(posting)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A posting with this title and company already exists")
    db.refresh(posting)
    _ensure_pipeline_entry(db, posting)
    db.commit()
    db.refresh(posting)
    return JobPostingRead.model_validate(posting)


@router.post("/import", response_model=ImportPreview)
def import_preview(data: ImportRequest):
    if data.url:
        try:
            return fetch_and_parse_url(data.url)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail="Could not fetch URL") from exc
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
        notes=data.notes,
        lead_source=data.lead_source,
    )
    db.add(posting)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = None
        match_reason = None
        if data.url:
            existing = db.query(JobPosting).filter(JobPosting.url == data.url).first()
            if existing:
                match_reason = "URL"
        if not existing and data.title and company:
            existing = db.query(JobPosting).filter(
                JobPosting.title == (data.title or "Untitled"),
                JobPosting.company_id == company.id,
            ).first()
            if existing:
                match_reason = "title and company"
        if existing:
            message = f"This posting already exists (matched by {match_reason})"
        else:
            message = "A posting with this title and company already exists"
        detail: dict = {"message": message}
        if existing:
            detail["existing_id"] = existing.id
        raise HTTPException(status_code=409, detail=detail)
    db.refresh(posting)
    _ensure_pipeline_entry(db, posting)
    db.commit()
    posting = db.query(JobPosting).options(
        joinedload(JobPosting.company), joinedload(JobPosting.pipeline_entry)
    ).filter(JobPosting.id == posting.id).first()
    result = JobPostingRead.model_validate(posting)
    result.pipeline_stage = posting.pipeline_entry.stage if posting.pipeline_entry else None
    return result


@router.get("/{posting_id}", response_model=JobPostingRead)
def get_posting(posting_id: int, db: Session = Depends(get_db)):
    posting = db.query(JobPosting).options(joinedload(JobPosting.company)).filter(JobPosting.id == posting_id).first()
    if not posting:
        raise HTTPException(status_code=404, detail="Posting not found")
    return posting


def _ensure_pipeline_entry(db: Session, posting: JobPosting) -> None:
    if posting.pipeline_entry is not None:
        return
    entry = PipelineEntry(job_posting_id=posting.id, stage="interested", position=0)
    db.add(entry)
    db.flush()
    history = PipelineHistory(
        pipeline_entry_id=entry.id, from_stage=None, to_stage="interested", event_type="stage_change"
    )
    db.add(history)


def _get_or_create_company(db: Session, name: str) -> Company:
    company = db.query(Company).filter(Company.name == name).first()
    if not company:
        company = Company(name=name)
        db.add(company)
        db.flush()
    return company


@router.put("/{posting_id}", response_model=JobPostingRead)
def update_posting(posting_id: int, data: JobPostingUpdate, db: Session = Depends(get_db)):
    posting = db.get(JobPosting, posting_id)
    if not posting:
        raise HTTPException(status_code=404, detail="Posting not found")
    update_dict = data.model_dump(exclude_unset=True)
    company_name = update_dict.pop("company_name", None)
    if company_name is not None:
        posting.company_id = _get_or_create_company(db, company_name).id
    for key, value in update_dict.items():
        setattr(posting, key, value)
    if posting.status == 'saved':
        _ensure_pipeline_entry(db, posting)
    db.commit()
    posting = db.query(JobPosting).options(
        joinedload(JobPosting.company), joinedload(JobPosting.pipeline_entry)
    ).filter(JobPosting.id == posting_id).first()
    result = JobPostingRead.model_validate(posting)
    result.pipeline_stage = posting.pipeline_entry.stage if posting.pipeline_entry else None
    return result


@router.post("/{posting_id}/summarize", response_model=JobPostingRead)
def summarize_posting_endpoint(posting_id: int, db: Session = Depends(get_db)):
    posting = db.get(JobPosting, posting_id)
    if not posting:
        raise HTTPException(status_code=404, detail="Posting not found")
    if not posting.raw_content:
        raise HTTPException(status_code=400, detail="No raw content available to summarize")
    try:
        summary = summarize_posting(posting.raw_content)
    except AIServiceError:
        raise HTTPException(status_code=503, detail="AI service unavailable — ensure Ollama is running")
    posting.description = summary
    db.commit()
    posting = db.query(JobPosting).options(
        joinedload(JobPosting.company), joinedload(JobPosting.pipeline_entry)
    ).filter(JobPosting.id == posting_id).first()
    result = JobPostingRead.model_validate(posting)
    result.pipeline_stage = posting.pipeline_entry.stage if posting.pipeline_entry else None
    return result


@router.post("/{posting_id}/save", response_model=JobPostingRead)
def save_posting(posting_id: int, db: Session = Depends(get_db)):
    posting = db.get(JobPosting, posting_id)
    if not posting:
        raise HTTPException(status_code=404, detail="Posting not found")
    posting.status = 'saved'
    _ensure_pipeline_entry(db, posting)
    db.commit()
    db.refresh(posting)
    data = JobPostingRead.model_validate(posting)
    data.pipeline_stage = posting.pipeline_entry.stage if posting.pipeline_entry else None
    return data


@router.post("/{posting_id}/dismiss", response_model=JobPostingRead)
def dismiss_posting(posting_id: int, db: Session = Depends(get_db)):
    posting = db.get(JobPosting, posting_id)
    if not posting:
        raise HTTPException(status_code=404, detail="Posting not found")
    posting.status = 'dismissed'
    db.commit()
    db.refresh(posting)
    data = JobPostingRead.model_validate(posting)
    data.pipeline_stage = posting.pipeline_entry.stage if posting.pipeline_entry else None
    return data


@router.post("/{posting_id}/dismiss-closed", response_model=JobPostingRead)
def dismiss_closed(posting_id: int, db: Session = Depends(get_db)):
    posting = db.query(JobPosting).options(
        joinedload(JobPosting.company), joinedload(JobPosting.pipeline_entry)
    ).filter(JobPosting.id == posting_id).first()
    if not posting:
        raise HTTPException(status_code=404, detail="Posting not found")
    posting.closed_check_dismissed = True
    db.commit()
    db.refresh(posting)
    result = JobPostingRead.model_validate(posting)
    result.pipeline_stage = posting.pipeline_entry.stage if posting.pipeline_entry else None
    return result


@router.delete("/{posting_id}", status_code=204)
def delete_posting(posting_id: int, db: Session = Depends(get_db)):
    posting = db.get(JobPosting, posting_id)
    if not posting:
        raise HTTPException(status_code=404, detail="Posting not found")
    db.delete(posting)
    db.commit()
    return Response(status_code=204)


@router.post("/{posting_id}/link-company", response_model=JobPostingRead)
def link_company(posting_id: int, db: Session = Depends(get_db)):
    posting = db.query(JobPosting).options(
        joinedload(JobPosting.company),
        joinedload(JobPosting.pipeline_entry)
    ).filter(JobPosting.id == posting_id).first()
    if not posting:
        raise HTTPException(status_code=404, detail="Posting not found")
    if posting.company_id:
        raise HTTPException(status_code=409, detail="Posting already linked to a company")
    if not posting.company_name:
        raise HTTPException(status_code=400, detail="No company name to save")

    company = db.query(Company).filter(Company.name == posting.company_name).first()
    if not company:
        company = Company(name=posting.company_name)
        db.add(company)
        db.flush()

    posting.company_id = company.id
    posting.company_name = None
    db.commit()
    db.refresh(posting)
    data = JobPostingRead.model_validate(posting)
    data.pipeline_stage = posting.pipeline_entry.stage if posting.pipeline_entry else None
    return data
