from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import PipelineEntry, JobPosting, InterviewNote
from app.schemas.dashboard import (
    ActionItemRead,
    DashboardResponse,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

INTERVIEW_LOOKBACK_DAYS = 7


@router.get("", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db)):
    now = datetime.utcnow()

    # Load all pipeline entries with their job postings and companies
    entries = (
        db.query(PipelineEntry)
        .options(
            joinedload(PipelineEntry.job_posting).joinedload(JobPosting.company)
        )
        .all()
    )

    # Lane counts
    lane_counts = dict(Counter(e.stage for e in entries))

    # Next-action items
    action_items: list[ActionItemRead] = []
    for entry in entries:
        if entry.next_action:
            posting = entry.job_posting
            is_overdue = (
                entry.next_action_date is not None and entry.next_action_date < now
            )
            action_items.append(
                ActionItemRead(
                    pipeline_entry_id=entry.id,
                    job_title=posting.title,
                    company_name=(
                        posting.company.name if posting.company else posting.company_name
                    ),
                    type="action",
                    description=entry.next_action,
                    date=str(entry.next_action_date) if entry.next_action_date else None,
                    is_overdue=is_overdue,
                )
            )

    # Interview items: no outcome, scheduled within lookback window
    cutoff = now - timedelta(days=INTERVIEW_LOOKBACK_DAYS)
    interview_notes = (
        db.query(InterviewNote)
        .options(
            joinedload(InterviewNote.pipeline_entry)
            .joinedload(PipelineEntry.job_posting)
            .joinedload(JobPosting.company)
        )
        .filter(
            InterviewNote.scheduled_at >= cutoff,
            InterviewNote.outcome.is_(None),
        )
        .all()
    )

    for note in interview_notes:
        entry = note.pipeline_entry
        posting = entry.job_posting
        is_overdue = note.scheduled_at is not None and note.scheduled_at < now
        action_items.append(
            ActionItemRead(
                pipeline_entry_id=entry.id,
                job_title=posting.title,
                company_name=(
                    posting.company.name if posting.company else posting.company_name
                ),
                type="interview",
                description=note.round,
                date=str(note.scheduled_at) if note.scheduled_at else None,
                is_overdue=is_overdue,
            )
        )

    # Sort: overdue first (oldest first), then upcoming (soonest first), undated last
    def sort_key(item):
        if item.is_overdue:
            return (0, item.date or "")
        elif item.date is not None:
            return (1, item.date)
        else:
            return (2, "")

    action_items.sort(key=sort_key)

    return DashboardResponse(lane_counts=lane_counts, action_items=action_items)
