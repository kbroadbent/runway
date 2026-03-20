from datetime import datetime
from pydantic import BaseModel, computed_field
from app.schemas.company import CompanyRead


class JobPostingCreate(BaseModel):
    title: str
    company_name: str | None = None
    company_id: int | None = None
    description: str | None = None
    location: str | None = None
    remote_type: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    url: str | None = None
    source: str = "manual"


class JobPostingUpdate(BaseModel):
    title: str | None = None
    company_name: str | None = None
    description: str | None = None
    location: str | None = None
    remote_type: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    url: str | None = None
    status: str | None = None
    tier: int | None = None


class JobPostingRead(BaseModel):
    id: int
    title: str
    company: CompanyRead | None
    description: str | None
    location: str | None
    remote_type: str | None
    salary_min: int | None
    salary_max: int | None
    url: str | None
    source: str
    date_posted: datetime | None
    date_saved: datetime
    status: str
    tier: int | None = None
    company_name: str | None = None
    pipeline_stage: str | None = None
    raw_content: str | None = None

    @computed_field
    @property
    def has_raw_content(self) -> bool:
        return self.raw_content is not None

    model_config = {"from_attributes": True}


class ImportRequest(BaseModel):
    text: str | None = None
    url: str | None = None


class ImportPreview(BaseModel):
    title: str | None = None
    company_name: str | None = None
    location: str | None = None
    remote_type: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    description: str | None = None
    url: str | None = None
    raw_content: str | None = None
    ai_used: bool = False
