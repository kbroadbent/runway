import pytest
import pandas as pd
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base
from app.models import SearchProfile
from app.services.search_service import run_search


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _profile(db, salary_min=None, exclude_terms=None):
    profile = SearchProfile(
        name="Test",
        sources='["indeed"]',
        salary_min=salary_min,
        exclude_terms=exclude_terms,
    )
    db.add(profile)
    db.flush()
    return profile


def _make_df(rows):
    """rows: list of dicts with keys: title, company, min_amount, max_amount, job_url"""
    defaults = {
        "description": None,
        "location": None,
        "is_remote": False,
        "site": "indeed",
        "date_posted": None,
    }
    return pd.DataFrame([{**defaults, **r} for r in rows])


@patch("app.services.search_service.scrape_jobs")
def test_salary_filter_excludes_below_min(mock_scrape, db):
    mock_scrape.return_value = _make_df([
        {"title": "Senior SWE", "company": "Acme", "min_amount": 200000, "max_amount": 220000, "job_url": "http://a.com/1"},
        {"title": "Junior SWE", "company": "Beta", "min_amount": 80000, "max_amount": 100000, "job_url": "http://a.com/2"},
    ])
    profile = _profile(db, salary_min=180000)
    result = run_search(profile, db)
    assert result["total_count"] == 2
    assert result["saved_count"] == 1  # only Senior SWE saved


@patch("app.services.search_service.scrape_jobs")
def test_salary_filter_excludes_no_salary(mock_scrape, db):
    """When min salary is set, listings with no salary info should be excluded."""
    mock_scrape.return_value = _make_df([
        {"title": "SWE", "company": "Acme", "min_amount": None, "max_amount": None, "job_url": "http://a.com/1"},
    ])
    profile = _profile(db, salary_min=180000)
    result = run_search(profile, db)
    assert result["saved_count"] == 0


@patch("app.services.search_service.scrape_jobs")
def test_salary_filter_keeps_no_salary_when_no_min(mock_scrape, db):
    """When no min salary is set, listings with no salary should be kept."""
    mock_scrape.return_value = _make_df([
        {"title": "SWE", "company": "Acme", "min_amount": None, "max_amount": None, "job_url": "http://a.com/1"},
    ])
    profile = _profile(db, salary_min=None)
    result = run_search(profile, db)
    assert result["saved_count"] == 1


@patch("app.services.search_service.scrape_jobs")
def test_salary_filter_keeps_partial_salary_above_min(mock_scrape, db):
    """If only min_amount is present and meets threshold, keep it."""
    mock_scrape.return_value = _make_df([
        {"title": "SWE", "company": "Acme", "min_amount": 200000, "max_amount": None, "job_url": "http://a.com/1"},
    ])
    profile = _profile(db, salary_min=180000)
    result = run_search(profile, db)
    assert result["saved_count"] == 1


@patch("app.services.search_service.scrape_jobs")
def test_exclude_terms_filters_by_title(mock_scrape, db):
    mock_scrape.return_value = _make_df([
        {"title": "Staff Engineer", "company": "Acme", "min_amount": None, "max_amount": None, "job_url": "http://a.com/1"},
        {"title": "Senior Engineer", "company": "Beta", "min_amount": None, "max_amount": None, "job_url": "http://a.com/2"},
    ])
    profile = _profile(db, exclude_terms='["staff"]')
    result = run_search(profile, db)
    assert result["saved_count"] == 1  # only Senior Engineer


@patch("app.services.search_service.scrape_jobs")
def test_exclude_terms_case_insensitive(mock_scrape, db):
    mock_scrape.return_value = _make_df([
        {"title": "STAFF ENGINEER", "company": "Acme", "min_amount": None, "max_amount": None, "job_url": "http://a.com/1"},
    ])
    profile = _profile(db, exclude_terms='["staff"]')
    result = run_search(profile, db)
    assert result["saved_count"] == 0
