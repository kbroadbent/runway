from datetime import datetime
from typing import Literal
from pydantic import BaseModel


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


class DashboardResponse(BaseModel):
    lane_counts: dict[str, int]
    action_items: list[NextActionItemRead | InterviewItemRead]
