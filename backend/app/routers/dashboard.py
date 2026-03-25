from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.constants import STAGE_GROUPS, STAGE_GROUP_ORDER
from app.database import get_db
from app.models import PipelineEntry, JobPosting
from app.schemas.dashboard import ActionItemRead, DashboardResponse

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db)):
    entries = db.query(PipelineEntry).options(
        joinedload(PipelineEntry.job_posting).joinedload(JobPosting.company)
    ).all()

    # Lane counts
    lane_counts = {lane: 0 for lane in STAGE_GROUP_ORDER}
    for entry in entries:
        lane = STAGE_GROUPS.get(entry.stage)
        if lane and lane in lane_counts:
            lane_counts[lane] += 1

    # Action items
    action_items = []
    for entry in entries:
        if entry.next_action:
            posting = entry.job_posting
            is_overdue = (
                entry.next_action_date is not None
                and entry.next_action_date < datetime.now()
            )
            action_items.append(ActionItemRead(
                pipeline_entry_id=entry.id,
                job_title=posting.title,
                company_name=posting.company.name if posting.company else posting.company_name,
                type="next_action",
                description=entry.next_action,
                date=entry.next_action_date.isoformat() if entry.next_action_date else None,
                is_overdue=is_overdue,
            ))

    return DashboardResponse(lane_counts=lane_counts, action_items=action_items)
