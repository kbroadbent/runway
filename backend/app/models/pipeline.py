from datetime import date, datetime
from sqlalchemy import Integer, String, Text, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class PipelineEntry(Base):
    __tablename__ = "pipeline_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_posting_id: Mapped[int] = mapped_column(ForeignKey("job_postings.id", ondelete="CASCADE"), unique=True)
    stage: Mapped[str] = mapped_column(String, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    next_action: Mapped[str | None] = mapped_column(String)
    next_action_date: Mapped[datetime | None] = mapped_column(DateTime)
    applied_date: Mapped[date | None] = mapped_column(Date)
    recruiter_screen_date: Mapped[date | None] = mapped_column(Date)
    manager_screen_date: Mapped[date | None] = mapped_column(Date)
    tech_screen_date: Mapped[date | None] = mapped_column(Date)
    onsite_date: Mapped[date | None] = mapped_column(Date)
    offer_date: Mapped[date | None] = mapped_column(Date)
    offer_expiration_date: Mapped[date | None] = mapped_column(Date)
    rejected_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    job_posting: Mapped["JobPosting"] = relationship(back_populates="pipeline_entry")
    interview_notes: Mapped[list["InterviewNote"]] = relationship(
        back_populates="pipeline_entry", cascade="all, delete-orphan"
    )
    history: Mapped[list["PipelineHistory"]] = relationship(
        back_populates="pipeline_entry", cascade="all, delete-orphan"
    )
    comments: Mapped[list["PipelineComment"]] = relationship(
        back_populates="pipeline_entry", cascade="all, delete-orphan"
    )
    custom_dates: Mapped[list["PipelineCustomDate"]] = relationship(
        back_populates="pipeline_entry", cascade="all, delete-orphan"
    )


class InterviewNote(Base):
    __tablename__ = "interview_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pipeline_entry_id: Mapped[int] = mapped_column(ForeignKey("pipeline_entries.id", ondelete="CASCADE"))
    round: Mapped[str] = mapped_column(String, nullable=False)
    scheduled_at: Mapped[date | None] = mapped_column(Date)
    interviewers: Mapped[str | None] = mapped_column(String)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    pipeline_entry: Mapped["PipelineEntry"] = relationship(back_populates="interview_notes")


class PipelineHistory(Base):
    __tablename__ = "pipeline_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pipeline_entry_id: Mapped[int] = mapped_column(ForeignKey("pipeline_entries.id", ondelete="CASCADE"))
    event_type: Mapped[str] = mapped_column(String, default="stage_change", server_default="stage_change")
    from_stage: Mapped[str | None] = mapped_column(String)
    to_stage: Mapped[str | None] = mapped_column(String)
    note: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text)
    event_date: Mapped[datetime | None] = mapped_column(DateTime)
    changed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    pipeline_entry: Mapped["PipelineEntry"] = relationship(back_populates="history")


class PipelineCustomDate(Base):
    __tablename__ = "pipeline_custom_dates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pipeline_entry_id: Mapped[int] = mapped_column(ForeignKey("pipeline_entries.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    pipeline_entry: Mapped["PipelineEntry"] = relationship(back_populates="custom_dates")
