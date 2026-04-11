from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import PipelineEntry, JobPosting, InterviewNote, PipelineHistory
from app.schemas.dashboard import (
    ActionItemRead,
    ClosedPostingAlert,
    DashboardResponse,
    FunnelResponse,
    FunnelTransition,
)
from app.constants import STAGE_GROUPS

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

INTERVIEW_LOOKBACK_DAYS = 7


@router.get("", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db)):
    now = datetime.now()

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

    upcoming_events: list[ActionItemRead] = []
    for note in interview_notes:
        entry = note.pipeline_entry
        posting = entry.job_posting
        is_overdue = note.scheduled_at is not None and note.scheduled_at < now
        upcoming_events.append(
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
    upcoming_events.sort(key=sort_key)

    # Closed posting alerts
    terminal_stages = {"rejected", "archived"}
    closed_postings_query = (
        db.query(JobPosting)
        .join(PipelineEntry)
        .filter(
            JobPosting.status == "saved",
            JobPosting.is_closed_detected == True,  # noqa: E712
            JobPosting.closed_check_dismissed == False,  # noqa: E712
            PipelineEntry.stage.notin_(terminal_stages),
        )
        .all()
    )
    closed_postings = [
        ClosedPostingAlert(
            id=p.id,
            title=p.title,
            company_name=p.company.name if p.company else p.company_name,
            url=p.url,
        )
        for p in closed_postings_query
    ]

    return DashboardResponse(
        lane_counts=lane_counts,
        upcoming_events=upcoming_events,
        action_items=action_items,
        closed_postings=closed_postings,
    )


@router.get("/funnel", response_model=FunnelResponse)
def get_funnel(
    start: str | None = None,
    end: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(PipelineHistory).filter(
        PipelineHistory.event_type == "stage_change",
        PipelineHistory.from_stage.isnot(None),
        PipelineHistory.to_stage.isnot(None),
    )

    if start:
        query = query.filter(PipelineHistory.changed_at >= datetime.fromisoformat(start))
    if end:
        query = query.filter(PipelineHistory.changed_at <= datetime.fromisoformat(end))

    history = query.all()

    # Collapse sub-lanes to parent stage groups
    transition_counts: dict[tuple[str, str], int] = {}
    for h in history:
        from_group = STAGE_GROUPS.get(h.from_stage, h.from_stage)
        to_group = STAGE_GROUPS.get(h.to_stage, h.to_stage)
        if from_group == to_group:
            continue  # skip intra-group transitions (e.g. scheduled→completed)
        key = (from_group, to_group)
        transition_counts[key] = transition_counts.get(key, 0) + 1

    transitions = [
        FunnelTransition(from_stage=k[0], to_stage=k[1], count=v)
        for k, v in transition_counts.items()
    ]

    # Current stage counts (also collapsed to groups)
    entries = db.query(PipelineEntry).all()
    group_counts: dict[str, int] = {}
    for e in entries:
        group = STAGE_GROUPS.get(e.stage, e.stage)
        group_counts[group] = group_counts.get(group, 0) + 1

    return FunnelResponse(transitions=transitions, stage_counts=group_counts)
