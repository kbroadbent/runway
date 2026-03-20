import pytest
import pandas as pd
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base
from app.models import SearchProfile, JobPosting, SearchResult
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


# --- Age-out tests ---

def _run_n_times(profile, db, dfs, mock_scrape):
    """Run search N times using successive DataFrames from dfs list."""
    for df in dfs:
        mock_scrape.return_value = df
        run_search(profile, db)


@patch("app.services.search_service.scrape_jobs")
def test_age_out_miss_increments(mock_scrape, db):
    """Second run with empty scrape → consecutive_misses == 1."""
    profile = _profile(db)
    first_df = _make_df([{"title": "SWE", "company": "Acme", "min_amount": None, "max_amount": None, "job_url": "http://a.com/1"}])
    empty_df = _make_df([])
    _run_n_times(profile, db, [first_df, empty_df], mock_scrape)

    posting = db.query(JobPosting).filter(JobPosting.url == "http://a.com/1").first()
    assert posting is not None
    assert posting.consecutive_misses == 1


@patch("app.services.search_service.scrape_jobs")
def test_age_out_miss_resets(mock_scrape, db):
    """Posting absent run 2, back in run 3 → consecutive_misses resets to 0."""
    profile = _profile(db)
    job_df = _make_df([{"title": "SWE", "company": "Acme", "min_amount": None, "max_amount": None, "job_url": "http://a.com/1"}])
    empty_df = _make_df([])
    _run_n_times(profile, db, [job_df, empty_df, job_df], mock_scrape)

    posting = db.query(JobPosting).filter(JobPosting.url == "http://a.com/1").first()
    assert posting is not None
    assert posting.consecutive_misses == 0


@patch("app.services.search_service.scrape_jobs")
def test_age_out_deletes_after_threshold(mock_scrape, db):
    """Posting absent 5 consecutive runs → deleted from DB and SearchResult gone."""
    profile = _profile(db)
    job_df = _make_df([{"title": "SWE", "company": "Acme", "min_amount": None, "max_amount": None, "job_url": "http://a.com/1"}])
    empty_df = _make_df([])
    _run_n_times(profile, db, [job_df] + [empty_df] * 5, mock_scrape)

    posting = db.query(JobPosting).filter(JobPosting.url == "http://a.com/1").first()
    assert posting is None
    result = db.query(SearchResult).filter(SearchResult.search_profile_id == profile.id).first()
    assert result is None


@patch("app.services.search_service.scrape_jobs")
def test_age_out_saved_immune(mock_scrape, db):
    """Posting saved before age-out runs → never deleted."""
    profile = _profile(db)
    job_df = _make_df([{"title": "SWE", "company": "Acme", "min_amount": None, "max_amount": None, "job_url": "http://a.com/1"}])
    empty_df = _make_df([])

    mock_scrape.return_value = job_df
    run_search(profile, db)

    # Save the posting
    posting = db.query(JobPosting).filter(JobPosting.url == "http://a.com/1").first()
    posting.status = 'saved'
    db.flush()

    _run_n_times(profile, db, [empty_df] * 5, mock_scrape)

    posting = db.query(JobPosting).filter(JobPosting.url == "http://a.com/1").first()
    assert posting is not None
    assert posting.status == 'saved'


@patch("app.services.search_service.scrape_jobs")
def test_age_out_multi_profile(mock_scrape, db):
    """Profile 1 ages out posting → profile 1's link deleted, posting and profile 2's link survive."""
    profile1 = _profile(db)
    profile2 = _profile(db)
    job_df = _make_df([{"title": "SWE", "company": "Acme", "min_amount": None, "max_amount": None, "job_url": "http://a.com/1"}])
    empty_df = _make_df([])

    # Both profiles discover the posting
    mock_scrape.return_value = job_df
    run_search(profile1, db)
    run_search(profile2, db)

    # Profile 1 runs 5 empty scrapes (ages out)
    _run_n_times(profile1, db, [empty_df] * 5, mock_scrape)

    # Posting still exists (profile 2 still has it)
    posting = db.query(JobPosting).filter(JobPosting.url == "http://a.com/1").first()
    assert posting is not None

    # Profile 1's link is gone
    p1_link = db.query(SearchResult).filter(
        SearchResult.search_profile_id == profile1.id,
        SearchResult.job_posting_id == posting.id,
    ).first()
    assert p1_link is None

    # Profile 2's link survives
    p2_link = db.query(SearchResult).filter(
        SearchResult.search_profile_id == profile2.id,
        SearchResult.job_posting_id == posting.id,
    ).first()
    assert p2_link is not None


@patch("app.services.search_service.scrape_jobs")
def test_age_out_raw_scrape_check_resets(mock_scrape, db):
    """Posting present in raw scrape but filtered by salary_min → consecutive_misses resets to 0."""
    profile = _profile(db, salary_min=200000)
    # First run: no salary filter, no min, so it gets saved with no salary_min on profile
    profile_no_filter = _profile(db)

    job_df = _make_df([{"title": "SWE", "company": "Acme", "min_amount": None, "max_amount": None, "job_url": "http://a.com/1"}])
    empty_df = _make_df([])

    # Save posting via profile with no filter
    mock_scrape.return_value = job_df
    run_search(profile_no_filter, db)

    posting = db.query(JobPosting).filter(JobPosting.url == "http://a.com/1").first()
    assert posting is not None

    # Manually link it to salary-filtered profile
    link = SearchResult(search_profile_id=profile.id, job_posting_id=posting.id, is_new=False)
    db.add(link)
    db.flush()

    # Run with salary-filtered profile — posting IS in raw scrape but filtered out
    # consecutive_misses should reset to 0 (seen in raw scrape)
    mock_scrape.return_value = job_df
    run_search(profile, db)

    db.refresh(posting)
    assert posting.consecutive_misses == 0


@patch("app.services.search_service.scrape_jobs")
def test_age_out_url_match_priority(mock_scrape, db):
    """Same URL, different title → still counts as seen (URL match wins)."""
    profile = _profile(db)
    job_df = _make_df([{"title": "SWE", "company": "Acme", "min_amount": None, "max_amount": None, "job_url": "http://a.com/1"}])
    different_title_df = _make_df([{"title": "Engineer", "company": "Acme", "min_amount": None, "max_amount": None, "job_url": "http://a.com/1"}])

    _run_n_times(profile, db, [job_df, different_title_df], mock_scrape)

    posting = db.query(JobPosting).filter(JobPosting.url == "http://a.com/1").first()
    assert posting is not None
    assert posting.consecutive_misses == 0
