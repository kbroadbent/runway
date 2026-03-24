from pydantic import BaseModel


class ActionItemRead(BaseModel):
    pipeline_entry_id: int
    job_title: str
    company_name: str | None
    type: str
    description: str
    date: str | None
    is_overdue: bool


class DashboardResponse(BaseModel):
    lane_counts: dict[str, int]
    action_items: list[ActionItemRead]
