from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import PipelineEntry, PipelineHistory, InterviewNote, JobPosting
from app.schemas.pipeline import (
    PipelineEntryCreate, PipelineEntryUpdate, PipelineMoveRequest, PipelineEntryRead,
    PipelineHistoryRead, InterviewNoteCreate, InterviewNoteUpdate, InterviewNoteRead,
)

router = APIRouter(tags=["pipeline"])

STAGES = ["interested", "applying", "applied", "recruiter_screen", "tech_screen", "onsite", "offer", "rejected", "archived"]


@router.get("/api/pipeline", response_model=dict[str, list[PipelineEntryRead]])
def list_pipeline(db: Session = Depends(get_db)):
    entries = db.query(PipelineEntry).options(
        joinedload(PipelineEntry.job_posting).joinedload(JobPosting.company)
    ).order_by(PipelineEntry.position).all()
    grouped = {stage: [] for stage in STAGES}
    for entry in entries:
        if entry.stage in grouped:
            grouped[entry.stage].append(entry)
    return grouped


@router.post("/api/pipeline", response_model=PipelineEntryRead, status_code=201)
def add_to_pipeline(data: PipelineEntryCreate, db: Session = Depends(get_db)):
    entry = PipelineEntry(job_posting_id=data.job_posting_id, stage=data.stage, position=0)
    db.add(entry)
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
    entry = db.get(PipelineEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Pipeline entry not found")
    old_stage = entry.stage
    entry.stage = data.to_stage
    history = PipelineHistory(
        pipeline_entry_id=entry.id, from_stage=old_stage, to_stage=data.to_stage, note=data.note
    )
    db.add(history)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/api/pipeline/{entry_id}/history", response_model=list[PipelineHistoryRead])
def get_pipeline_history(entry_id: int, db: Session = Depends(get_db)):
    return db.query(PipelineHistory).filter(PipelineHistory.pipeline_entry_id == entry_id).order_by(PipelineHistory.changed_at).all()


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
