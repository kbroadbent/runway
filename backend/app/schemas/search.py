from datetime import datetime
from pydantic import BaseModel


class SearchProfileCreate(BaseModel):
    name: str
    search_term: str | None = None
    location: str | None = None
    remote_filter: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    job_type: str | None = None
    sources: list[str] | None = None
    exclude_terms: list[str] | None = None
    run_interval: int | None = None
    is_auto_enabled: bool = False


class SearchProfileUpdate(BaseModel):
    name: str | None = None
    search_term: str | None = None
    location: str | None = None
    remote_filter: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    job_type: str | None = None
    sources: list[str] | None = None
    exclude_terms: list[str] | None = None
    run_interval: int | None = None
    is_auto_enabled: bool | None = None


class SearchProfileRead(BaseModel):
    id: int
    name: str
    search_term: str | None
    location: str | None
    remote_filter: str | None
    salary_min: int | None
    salary_max: int | None
    job_type: str | None
    sources: list[str] | None
    exclude_terms: list[str] | None
    run_interval: int | None
    is_auto_enabled: bool
    created_at: datetime
    last_run_at: datetime | None
    new_result_count: int = 0

    model_config = {"from_attributes": True}


class SearchRunResult(BaseModel):
    new_count: int
    total_count: int


class SearchResultRead(BaseModel):
    id: int
    job_posting_id: int
    run_date: datetime
    is_new: bool

    model_config = {"from_attributes": True}
