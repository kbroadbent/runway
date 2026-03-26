"""Tests for SearchResult deduplication.

Verifies that running a search multiple times for the same profile does not
create duplicate SearchResult rows for the same (search_profile_id, job_posting_id) pair.
"""
import pytest
import pandas as pd
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base
from app.models import SearchProfile, JobPosting, SearchResult, Company
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


def _profile(db):
    profile = SearchProfile(
        name="Test",
        sources='["indeed"]',
    )
    db.add(profile)
    db.flush()
    return profile


def _make_df(rows):
    defaults = {
        "description": None,
        "location": None,
        "is_remote": False,
        "site": "indeed",
        "date_posted": None,
    }
    return pd.DataFrame([{**defaults, **r} for r in rows])


# --- UniqueConstraint tests ---


def test_unique_constraint_prevents_duplicate_search_result(db):
    """DB should reject a second SearchResult with same (search_profile_id, job_posting_id)."""
    profile = _profile(db)
    company = Company(name="Acme")
    db.add(company)
    db.flush()
    posting = JobPosting(
        title="SWE", company_id=company.id, company_name="Acme",
        location="", url="http://a.com/1", source="indeed", status="unsaved",
    )
    db.add(posting)
    db.flush()

    r1 = SearchResult(search_profile_id=profile.id, job_posting_id=posting.id, is_new=True)
    db.add(r1)
    db.flush()

    r2 = SearchResult(search_profile_id=profile.id, job_posting_id=posting.id, is_new=False)
    db.add(r2)
    with pytest.raises(IntegrityError):
        db.flush()


def test_unique_constraint_allows_different_profiles_same_posting(db):
    """Two different profiles linking to the same posting should be allowed."""
    p1 = _profile(db)
    p2 = _profile(db)
    company = Company(name="Acme")
    db.add(company)
    db.flush()
    posting = JobPosting(
        title="SWE", company_id=company.id, company_name="Acme",
        location="", url="http://a.com/1", source="indeed", status="unsaved",
    )
    db.add(posting)
    db.flush()

    db.add(SearchResult(search_profile_id=p1.id, job_posting_id=posting.id, is_new=True))
    db.add(SearchResult(search_profile_id=p2.id, job_posting_id=posting.id, is_new=True))
    db.flush()  # should not raise

    count = db.query(SearchResult).filter(SearchResult.job_posting_id == posting.id).count()
    assert count == 2


# --- Service-level dedup tests ---


@patch("app.services.search_service.scrape_jobs")
def test_run_search_twice_does_not_duplicate_new_posting(mock_scrape, db):
    """Running search twice with the same posting should produce exactly one SearchResult."""
    profile = _profile(db)
    job_df = _make_df([
        {"title": "SWE", "company": "Acme", "min_amount": None, "max_amount": None, "job_url": "http://a.com/1"},
    ])
    mock_scrape.return_value = job_df
    run_search(profile, db)

    mock_scrape.return_value = job_df
    run_search(profile, db)

    results = db.query(SearchResult).filter(
        SearchResult.search_profile_id == profile.id,
    ).all()
    assert len(results) == 1


@patch("app.services.search_service.scrape_jobs")
def test_run_search_twice_does_not_duplicate_existing_posting(mock_scrape, db):
    """An existing posting seen again by the same profile should not create a second SearchResult."""
    profile = _profile(db)
    company = Company(name="Acme")
    db.add(company)
    db.flush()
    posting = JobPosting(
        title="SWE", company_id=company.id, company_name="Acme",
        location="", url="http://a.com/1", source="indeed", status="unsaved",
    )
    db.add(posting)
    db.flush()
    # Pre-existing link
    db.add(SearchResult(search_profile_id=profile.id, job_posting_id=posting.id, is_new=True))
    db.flush()

    job_df = _make_df([
        {"title": "SWE", "company": "Acme", "min_amount": None, "max_amount": None, "job_url": "http://a.com/1"},
    ])
    mock_scrape.return_value = job_df
    run_search(profile, db)

    count = db.query(SearchResult).filter(
        SearchResult.search_profile_id == profile.id,
        SearchResult.job_posting_id == posting.id,
    ).count()
    assert count == 1


@patch("app.services.search_service.scrape_jobs")
def test_run_search_updates_run_date_on_re_seen_posting(mock_scrape, db):
    """When a posting is seen again, the existing SearchResult's run_date should be updated."""
    profile = _profile(db)
    job_df = _make_df([
        {"title": "SWE", "company": "Acme", "min_amount": None, "max_amount": None, "job_url": "http://a.com/1"},
    ])
    mock_scrape.return_value = job_df
    run_search(profile, db)

    result = db.query(SearchResult).filter(
        SearchResult.search_profile_id == profile.id,
    ).one()
    first_run_date = result.run_date

    mock_scrape.return_value = job_df
    run_search(profile, db)

    db.refresh(result)
    assert result.run_date >= first_run_date


@patch("app.services.search_service.scrape_jobs")
def test_dedup_different_profiles_still_create_separate_results(mock_scrape, db):
    """Two profiles finding the same posting should each get their own SearchResult."""
    p1 = _profile(db)
    p2 = _profile(db)
    job_df = _make_df([
        {"title": "SWE", "company": "Acme", "min_amount": None, "max_amount": None, "job_url": "http://a.com/1"},
    ])
    mock_scrape.return_value = job_df
    run_search(p1, db)
    mock_scrape.return_value = job_df
    run_search(p2, db)

    total = db.query(SearchResult).filter(
        SearchResult.job_posting_id == db.query(JobPosting).filter(JobPosting.url == "http://a.com/1").first().id,
    ).count()
    assert total == 2


@patch("app.services.search_service.scrape_jobs")
def test_dedup_by_title_company_match(mock_scrape, db):
    """Posting matched by title+company (not URL) should also be deduped on second run."""
    profile = _profile(db)
    # First run creates posting
    job_df = _make_df([
        {"title": "SWE", "company": "Acme", "min_amount": None, "max_amount": None, "job_url": "http://a.com/1"},
    ])
    mock_scrape.return_value = job_df
    run_search(profile, db)

    # Second run: same title+company but different URL
    job_df2 = _make_df([
        {"title": "SWE", "company": "Acme", "min_amount": None, "max_amount": None, "job_url": "http://a.com/99"},
    ])
    mock_scrape.return_value = job_df2
    run_search(profile, db)

    results = db.query(SearchResult).filter(
        SearchResult.search_profile_id == profile.id,
    ).all()
    assert len(results) == 1
