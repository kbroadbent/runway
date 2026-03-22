from datetime import datetime
from sqlalchemy import Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class PipelineComment(Base):
    __tablename__ = "pipeline_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pipeline_entry_id: Mapped[int] = mapped_column(ForeignKey("pipeline_entries.id", ondelete="CASCADE"))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    pipeline_entry: Mapped["PipelineEntry"] = relationship(back_populates="comments")
