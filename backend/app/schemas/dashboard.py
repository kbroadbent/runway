from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class ActionItemRead(BaseModel):
    pipeline_entry_id: int
    job_title: str
    company_name: str | None
    type: str
    description: str
    date: str | None
    is_overdue: bool


class NextActionItemRead(BaseModel):
    pipeline_entry_id: int
    job_title: str
    company_name: str | None
    type: Literal["action"]
    description: str
    date: datetime | None
    is_overdue: bool


class InterviewItemRead(BaseModel):
    pipeline_entry_id: int
    job_title: str
    company_name: str | None
    type: Literal["interview"]
    description: str
    date: datetime | None
    is_overdue: bool


class StaleEntryRead(BaseModel):
    pipeline_entry_id: int
    job_title: str
    company_name: str | None
    stage: str
    days_in_stage: int


class ClosedPostingAlert(BaseModel):
    id: int
    title: str
    company_name: str | None
    url: str | None


class FunnelTransition(BaseModel):
    from_stage: str
    to_stage: str
    count: int


class FunnelResponse(BaseModel):
    transitions: list[FunnelTransition]
    stage_counts: dict[str, int]


class DashboardResponse(BaseModel):
    lane_counts: dict[str, int]
    upcoming_events: list[ActionItemRead]
    action_items: list[ActionItemRead]
    stale_entries: list[StaleEntryRead] = []
    closed_postings: list[ClosedPostingAlert] = []
