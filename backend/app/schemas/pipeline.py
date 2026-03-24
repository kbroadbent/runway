from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.job_posting import JobPostingRead


class PipelineEntryCreate(BaseModel):
    job_posting_id: int
    stage: str = "interested"


class PipelineEntryUpdate(BaseModel):
    next_action: str | None = None
    next_action_date: datetime | None = None


class PipelineMoveRequest(BaseModel):
    to_stage: str
    note: str | None = None


class ManualEventCreate(BaseModel):
    description: str = Field(..., max_length=10000)
    event_date: datetime | None = None


class PipelineEntryRead(BaseModel):
    id: int
    job_posting: JobPostingRead
    stage: str
    position: int
    next_action: str | None
    next_action_date: datetime | None
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
    scheduled_at: datetime | None = None
    interviewers: str | None = None
    notes: str | None = None
    outcome: str | None = None


class InterviewNoteUpdate(BaseModel):
    round: str | None = None
    scheduled_at: datetime | None = None
    interviewers: str | None = None
    notes: str | None = None
    outcome: str | None = None


class InterviewNoteRead(BaseModel):
    id: int
    round: str
    scheduled_at: datetime | None
    interviewers: str | None
    notes: str | None
    outcome: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
