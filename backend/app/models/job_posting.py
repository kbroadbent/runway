from datetime import datetime
from sqlalchemy import Boolean, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class JobPosting(Base):
    __tablename__ = "job_postings"
    __table_args__ = (
        UniqueConstraint("url", name="uq_job_postings_url"),
        UniqueConstraint("title", "company_id", name="uq_job_postings_title_company"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"))
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String)
    remote_type: Mapped[str | None] = mapped_column(String)
    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    url: Mapped[str | None] = mapped_column(String)
    source: Mapped[str] = mapped_column(String, nullable=False)
    date_posted: Mapped[datetime | None] = mapped_column(DateTime)
    date_saved: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    status: Mapped[str] = mapped_column(String, default='saved')
    raw_content: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    company_name: Mapped[str | None] = mapped_column(String)
    tier: Mapped[int | None] = mapped_column(Integer)
    consecutive_misses: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    lead_source: Mapped[str] = mapped_column(String, nullable=False, server_default="cold_apply")
    is_closed_detected: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", nullable=False)
    closed_check_dismissed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", nullable=False)

    company: Mapped["Company"] = relationship(back_populates="postings")
    pipeline_entry: Mapped["PipelineEntry | None"] = relationship(
        back_populates="job_posting", cascade="all, delete-orphan", uselist=False
    )
    search_results: Mapped[list["SearchResult"]] = relationship(back_populates="job_posting", cascade="all, delete-orphan", passive_deletes=True)
