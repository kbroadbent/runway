from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import PipelineEntry, PipelineHistory, InterviewNote, JobPosting, PipelineComment, PipelineCustomDate, Company
from app.schemas.pipeline import (
    PipelineEntryCreate, PipelineEntryUpdate, PipelineMoveRequest, PipelineEntryRead,
    PipelineHistoryRead, InterviewNoteCreate, InterviewNoteUpdate, InterviewNoteRead,
    ManualEventCreate, CustomDateCreate, CustomDateUpdate, CustomDateRead,
)
from app.schemas.pipeline_comment import PipelineCommentCreate, PipelineCommentUpdate, PipelineCommentRead
from app.constants import STAGES, VALID_STAGES
from app.schemas.job_posting import VALID_LEAD_SOURCES

router = APIRouter(tags=["pipeline"])


def _validate_stage(stage: str) -> None:
    if stage not in VALID_STAGES:
        raise HTTPException(status_code=422, detail=f"Invalid stage '{stage}'. Must be one of: {', '.join(STAGES)}")


@router.get("/api/pipeline", response_model=dict[str, list[PipelineEntryRead]])
def list_pipeline(
    search: str | None = None,
    tier: int | None = None,
    lead_source: str | None = None,
    db: Session = Depends(get_db),
):
    if tier is not None and tier not in (1, 2, 3):
        raise HTTPException(status_code=422, detail="Tier must be 1, 2, or 3")
    if lead_source is not None and lead_source not in VALID_LEAD_SOURCES:
        raise HTTPException(status_code=422, detail=f"Invalid lead_source '{lead_source}'. Must be one of: {', '.join(sorted(VALID_LEAD_SOURCES))}")

    query = db.query(PipelineEntry).options(
        joinedload(PipelineEntry.job_posting).joinedload(JobPosting.company)
    )

    if search or tier is not None or lead_source is not None:
        query = query.join(JobPosting)
        if search:
            query = query.outerjoin(Company, JobPosting.company_id == Company.id)
            query = query.filter(or_(
                JobPosting.title.ilike(f"%{search}%"),
                JobPosting.company_name.ilike(f"%{search}%"),
                Company.name.ilike(f"%{search}%"),
            ))
        if tier is not None:
            query = query.filter(JobPosting.tier == tier)
        if lead_source is not None:
            query = query.filter(JobPosting.lead_source == lead_source)

    entries = query.order_by(PipelineEntry.position).all()
    grouped = {stage: [] for stage in STAGES}
    for entry in entries:
        if entry.stage in grouped:
            grouped[entry.stage].append(entry)
    return grouped


@router.post("/api/pipeline", response_model=PipelineEntryRead, status_code=201)
def add_to_pipeline(data: PipelineEntryCreate, db: Session = Depends(get_db)):
    _validate_stage(data.stage)
    posting = db.get(JobPosting, data.job_posting_id)
    if not posting:
        raise HTTPException(status_code=404, detail="Job posting not found")
    if posting.status == 'unsaved':
        posting.status = 'saved'
    entry = PipelineEntry(job_posting_id=data.job_posting_id, stage=data.stage, position=0)
    db.add(entry)
    db.flush()
    history = PipelineHistory(pipeline_entry_id=entry.id, from_stage=None, to_stage=data.stage, event_type="stage_change")
    db.add(history)
    db.commit()
    db.refresh(entry)
    return entry


@router.put("/api/pipeline/{entry_id}", response_model=PipelineEntryRead)
def update_pipeline_entry(entry_id: int, data: PipelineEntryUpdate, db: Session = Depends(get_db)):
    entry = db.get(PipelineEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Pipeline entry not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return entry


@router.put("/api/pipeline/{entry_id}/move", response_model=PipelineEntryRead)
def move_pipeline_entry(entry_id: int, data: PipelineMoveRequest, db: Session = Depends(get_db)):
    _validate_stage(data.to_stage)
    entry = db.get(PipelineEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Pipeline entry not found")
    old_stage = entry.stage
    entry.stage = data.to_stage
    if data.stage_dates:
        valid_date_fields = {"applied_date", "recruiter_screen_date", "tech_screen_date",
                             "onsite_date", "offer_date", "offer_expiration_date"}
        for field, value in data.stage_dates.items():
            if field in valid_date_fields:
                setattr(entry, field, value)
    history = PipelineHistory(
        pipeline_entry_id=entry.id, from_stage=old_stage, to_stage=data.to_stage, note=data.note, event_type="stage_change"
    )
    db.add(history)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/api/pipeline/{entry_id}/history", response_model=list[PipelineHistoryRead])
def get_pipeline_history(entry_id: int, db: Session = Depends(get_db)):
    return db.query(PipelineHistory).filter(PipelineHistory.pipeline_entry_id == entry_id).order_by(PipelineHistory.changed_at).all()


@router.post("/api/pipeline/{entry_id}/history", response_model=PipelineHistoryRead, status_code=201)
def add_manual_event(entry_id: int, data: ManualEventCreate, db: Session = Depends(get_db)):
    entry = db.get(PipelineEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Pipeline entry not found")
    event = PipelineHistory(
        pipeline_entry_id=entry_id,
        event_type="manual",
        description=data.description,
        event_date=data.event_date,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("/api/pipeline/{entry_id}/interviews", response_model=list[InterviewNoteRead])
def list_interviews(entry_id: int, db: Session = Depends(get_db)):
    return db.query(InterviewNote).filter(InterviewNote.pipeline_entry_id == entry_id).order_by(InterviewNote.created_at).all()


@router.post("/api/pipeline/{entry_id}/interviews", response_model=InterviewNoteRead, status_code=201)
def add_interview(entry_id: int, data: InterviewNoteCreate, db: Session = Depends(get_db)):
    entry = db.get(PipelineEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Pipeline entry not found")
    note = InterviewNote(pipeline_entry_id=entry_id, **data.model_dump())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.put("/api/interviews/{note_id}", response_model=InterviewNoteRead)
def update_interview(note_id: int, data: InterviewNoteUpdate, db: Session = Depends(get_db)):
    note = db.get(InterviewNote, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Interview note not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(note, key, value)
    db.commit()
    db.refresh(note)
    return note


@router.delete("/api/interviews/{note_id}", status_code=204)
def delete_interview(note_id: int, db: Session = Depends(get_db)):
    note = db.get(InterviewNote, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Interview note not found")
    db.delete(note)
    db.commit()
    return Response(status_code=204)


# --- Comments ---

@router.get("/api/pipeline/{entry_id}/comments", response_model=list[PipelineCommentRead])
def list_comments(entry_id: int, db: Session = Depends(get_db)):
    return db.query(PipelineComment).filter(
        PipelineComment.pipeline_entry_id == entry_id
    ).order_by(PipelineComment.created_at).all()


@router.post("/api/pipeline/{entry_id}/comments", response_model=PipelineCommentRead, status_code=201)
def add_comment(entry_id: int, data: PipelineCommentCreate, db: Session = Depends(get_db)):
    entry = db.get(PipelineEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Pipeline entry not found")
    comment = PipelineComment(pipeline_entry_id=entry_id, content=data.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.put("/api/pipeline-comments/{comment_id}", response_model=PipelineCommentRead)
def update_comment(comment_id: int, data: PipelineCommentUpdate, db: Session = Depends(get_db)):
    comment = db.get(PipelineComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    comment.content = data.content
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/api/pipeline-comments/{comment_id}", status_code=204)
def delete_comment(comment_id: int, db: Session = Depends(get_db)):
    comment = db.get(PipelineComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    db.delete(comment)
    db.commit()
    return Response(status_code=204)


# --- Custom Dates ---

@router.get("/api/pipeline/{entry_id}/dates", response_model=list[CustomDateRead])
def list_custom_dates(entry_id: int, db: Session = Depends(get_db)):
    entry = db.get(PipelineEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Pipeline entry not found")
    return db.query(PipelineCustomDate).filter(
        PipelineCustomDate.pipeline_entry_id == entry_id
    ).order_by(PipelineCustomDate.date).all()


@router.post("/api/pipeline/{entry_id}/dates", response_model=CustomDateRead, status_code=201)
def create_custom_date(entry_id: int, data: CustomDateCreate, db: Session = Depends(get_db)):
    entry = db.get(PipelineEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Pipeline entry not found")
    custom = PipelineCustomDate(pipeline_entry_id=entry_id, label=data.label, date=data.date)
    db.add(custom)
    db.commit()
    db.refresh(custom)
    return custom


@router.put("/api/pipeline/{entry_id}/dates/{date_id}", response_model=CustomDateRead)
def update_custom_date(entry_id: int, date_id: int, data: CustomDateUpdate, db: Session = Depends(get_db)):
    custom = db.query(PipelineCustomDate).filter(
        PipelineCustomDate.id == date_id,
        PipelineCustomDate.pipeline_entry_id == entry_id,
    ).first()
    if not custom:
        raise HTTPException(status_code=404, detail="Custom date not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(custom, key, value)
    db.commit()
    db.refresh(custom)
    return custom


@router.delete("/api/pipeline/{entry_id}/dates/{date_id}", status_code=204)
def delete_custom_date(entry_id: int, date_id: int, db: Session = Depends(get_db)):
    custom = db.query(PipelineCustomDate).filter(
        PipelineCustomDate.id == date_id,
        PipelineCustomDate.pipeline_entry_id == entry_id,
    ).first()
    if not custom:
        raise HTTPException(status_code=404, detail="Custom date not found")
    db.delete(custom)
    db.commit()
    return Response(status_code=204)
