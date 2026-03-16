from datetime import datetime
from sqlalchemy import Integer, String, Float, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    website: Mapped[str | None] = mapped_column(String)
    glassdoor_rating: Mapped[float | None] = mapped_column(Float)
    glassdoor_url: Mapped[str | None] = mapped_column(String)
    levels_salary_data: Mapped[str | None] = mapped_column(Text)  # JSON string
    levels_url: Mapped[str | None] = mapped_column(String)
    blind_url: Mapped[str | None] = mapped_column(String)
    employee_count: Mapped[int | None] = mapped_column(Integer)
    industry: Mapped[str | None] = mapped_column(String)
    notes: Mapped[str | None] = mapped_column(Text)
    last_researched_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    postings: Mapped[list["JobPosting"]] = relationship(back_populates="company")
