from datetime import date as Date, datetime
from typing import Annotated, Optional
from pydantic import BaseModel, BeforeValidator, Field
from app.schemas.job_posting import JobPostingRead


def _coerce_to_date(v):
    """Accept date, datetime, or ISO datetime string and return a date."""
    if v is None:
        return v
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, Date):
        return v
    if isinstance(v, str):
        try:
            return datetime.fromisoformat(v).date()
        except ValueError:
            return Date.fromisoformat(v)
    return v


FlexDate = Annotated[Date, BeforeValidator(_coerce_to_date)]


class PipelineEntryCreate(BaseModel):
    job_posting_id: int
    stage: str = "interested"


class PipelineEntryUpdate(BaseModel):
    next_action: str | None = None
    next_action_date: datetime | None = None
    applied_date: Optional[FlexDate] = None
    recruiter_screen_date: Optional[FlexDate] = None
    manager_screen_date: Optional[FlexDate] = None
    tech_screen_date: Optional[FlexDate] = None
    onsite_date: Optional[FlexDate] = None
    offer_date: Optional[FlexDate] = None
    offer_expiration_date: Optional[FlexDate] = None
    rejected_date: Optional[FlexDate] = None


class PipelineMoveRequest(BaseModel):
    to_stage: str
    note: str | None = None
    stage_dates: Optional[dict[str, Optional[Date]]] = None


class ManualEventCreate(BaseModel):
    description: str = Field(..., max_length=10000)
    event_date: datetime | None = None


class CustomDateCreate(BaseModel):
    label: str = Field(..., min_length=1, max_length=100)
    date: Date


class CustomDateUpdate(BaseModel):
    label: Optional[str] = Field(default=None, min_length=1, max_length=100)
    date: Optional[Date] = None


class CustomDateRead(BaseModel):
    id: int
    label: str
    date: Date
    created_at: datetime

    model_config = {"from_attributes": True}


class PipelineEntryRead(BaseModel):
    id: int
    job_posting: JobPostingRead
    stage: str
    position: int
    next_action: str | None
    next_action_date: datetime | None
    applied_date: Optional[Date] = None
    recruiter_screen_date: Optional[Date] = None
    manager_screen_date: Optional[Date] = None
    tech_screen_date: Optional[Date] = None
    onsite_date: Optional[Date] = None
    offer_date: Optional[Date] = None
    offer_expiration_date: Optional[Date] = None
    rejected_date: Optional[Date] = None
    custom_dates: list[CustomDateRead] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PipelineHistoryRead(BaseModel):
    id: int
    event_type: str
    from_stage: str | None
    to_stage: str | None
    note: str | None
    description: str | None
    event_date: datetime | None
    changed_at: datetime

    model_config = {"from_attributes": True}


class InterviewNoteCreate(BaseModel):
    round: str
    scheduled_at: Optional[FlexDate] = None
    interviewers: str | None = None
    notes: str | None = None


class InterviewNoteUpdate(BaseModel):
    round: str | None = None
    scheduled_at: Optional[FlexDate] = None
    interviewers: str | None = None
    notes: str | None = None


class InterviewNoteRead(BaseModel):
    id: int
    round: str
    scheduled_at: Date | None
    interviewers: str | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
