from datetime import datetime
from pydantic import BaseModel


class CompanyCreate(BaseModel):
    name: str
    website: str | None = None
    industry: str | None = None
    employee_count: int | None = None
    notes: str | None = None


class CompanyUpdate(BaseModel):
    name: str | None = None
    website: str | None = None
    glassdoor_rating: float | None = None
    glassdoor_url: str | None = None
    levels_salary_data: str | None = None
    levels_url: str | None = None
    blind_url: str | None = None
    employee_count: int | None = None
    industry: str | None = None
    notes: str | None = None
    common_questions: str | None = None


class CompanyRead(BaseModel):
    id: int
    name: str
    website: str | None
    glassdoor_rating: float | None
    glassdoor_url: str | None
    levels_salary_data: str | None
    levels_url: str | None
    blind_url: str | None
    employee_count: int | None
    industry: str | None
    notes: str | None
    common_questions: str | None
    last_researched_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CompanyInterviewRead(BaseModel):
    id: int
    round: str
    scheduled_at: datetime | None
    interviewers: str | None
    notes: str | None
    outcome: str | None
    created_at: datetime
    posting_id: int
    posting_title: str

    model_config = {"from_attributes": True}
