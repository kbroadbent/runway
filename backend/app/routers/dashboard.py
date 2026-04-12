from collections import Counter
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import PipelineEntry, JobPosting, PipelineHistory
from app.schemas.dashboard import (
    ActionItemRead,
    ClosedPostingAlert,
    DashboardResponse,
    FunnelResponse,
    FunnelTransition,
    StaleEntryRead,
)
from app.constants import STAGE_GROUPS

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])



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

    # Upcoming events from pipeline entry key dates (today or later)
    today = date.today()
    interview_date_fields = {
        "recruiter_screen_date": "Recruiter Screen",
        "manager_screen_date": "Manager Screen",
        "tech_screen_date": "Tech Screen",
        "onsite_date": "Onsite",
    }

    upcoming_events: list[ActionItemRead] = []
    for entry in entries:
        posting = entry.job_posting
        for field, label in interview_date_fields.items():
            d = getattr(entry, field, None)
            if d is not None and d >= today:
                upcoming_events.append(
                    ActionItemRead(
                        pipeline_entry_id=entry.id,
                        job_title=posting.title,
                        company_name=(
                            posting.company.name if posting.company else posting.company_name
                        ),
                        type="interview",
                        description=label,
                        date=str(d),
                        is_overdue=False,
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

    # Stale entries: applied or later, non-terminal, unchanged for 7+ days
    pre_funnel_stages = {"interested", "applying"}
    terminal_stages_stale = {"rejected", "withdrawn", "archived"}
    stale_threshold = now - timedelta(days=7)
    stale_entries = []
    for entry in entries:
        if entry.stage in pre_funnel_stages or entry.stage in terminal_stages_stale:
            continue
        has_future_date = any(
            getattr(entry, f, None) is not None and getattr(entry, f) >= today
            for f in interview_date_fields
        )
        if has_future_date:
            continue
        if entry.updated_at <= stale_threshold:
            posting = entry.job_posting
            days = (now - entry.updated_at).days
            stale_entries.append(
                StaleEntryRead(
                    pipeline_entry_id=entry.id,
                    job_title=posting.title,
                    company_name=(
                        posting.company.name if posting.company else posting.company_name
                    ),
                    stage=entry.stage,
                    days_in_stage=days,
                )
            )
    stale_entries.sort(key=lambda x: x.days_in_stage, reverse=True)

    return DashboardResponse(
        lane_counts=lane_counts,
        upcoming_events=upcoming_events,
        action_items=action_items,
        stale_entries=stale_entries,
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
    # Remap pre-funnel stages to "Applied" so jobs that skip straight
    # to a terminal stage (e.g. Applying→Withdrawn) still appear in the chart
    pre_funnel_stages = {"Interested", "Applying"}
    transition_counts: dict[tuple[str, str], int] = {}
    for h in history:
        from_group = STAGE_GROUPS.get(h.from_stage, h.from_stage)
        to_group = STAGE_GROUPS.get(h.to_stage, h.to_stage)
        if from_group in pre_funnel_stages:
            from_group = "Applied"
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

    # Add "Still Active" synthetic transitions for non-terminal stages
    terminal_stages = {"Rejected", "Withdrawn", "Archived", "Interested", "Applying"}
    for stage, count in group_counts.items():
        if stage not in terminal_stages and count > 0:
            transitions.append(
                FunnelTransition(from_stage=stage, to_stage="Still Active", count=count)
            )

    return FunnelResponse(transitions=transitions, stage_counts=group_counts)
