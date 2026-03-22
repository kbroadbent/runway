from datetime import datetime
from pydantic import BaseModel, Field


class PipelineCommentCreate(BaseModel):
    content: str = Field(..., max_length=10000)


class PipelineCommentUpdate(BaseModel):
    content: str = Field(..., max_length=10000)


class PipelineCommentRead(BaseModel):
    id: int
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
