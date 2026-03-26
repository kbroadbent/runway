from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, Boolean, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class SearchProfile(Base):
    __tablename__ = "search_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    search_term: Mapped[str | None] = mapped_column(String)
    location: Mapped[str | None] = mapped_column(String)
    remote_filter: Mapped[str | None] = mapped_column(String)
    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    job_type: Mapped[str | None] = mapped_column(String)
    sources: Mapped[str | None] = mapped_column(Text)  # JSON array string
    exclude_terms: Mapped[str | None] = mapped_column(Text)  # JSON array string
    run_interval: Mapped[int | None] = mapped_column(Integer)
    is_auto_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime)

    results: Mapped[list["SearchResult"]] = relationship(
        back_populates="search_profile", cascade="all, delete-orphan"
    )


class SearchResult(Base):
    __tablename__ = "search_results"
    __table_args__ = (
        UniqueConstraint("search_profile_id", "job_posting_id", name="uq_search_result_profile_posting"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    search_profile_id: Mapped[int] = mapped_column(ForeignKey("search_profiles.id", ondelete="CASCADE"))
    job_posting_id: Mapped[int] = mapped_column(ForeignKey("job_postings.id"))
    run_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_new: Mapped[bool] = mapped_column(Boolean, default=True)

    search_profile: Mapped["SearchProfile"] = relationship(back_populates="results")
    job_posting: Mapped["JobPosting"] = relationship(back_populates="search_results")
