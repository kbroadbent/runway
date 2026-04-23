import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Company, JobPosting, PipelineEntry, InterviewNote, PipelineHistory, SearchProfile, SearchResult


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_tables_created(db):
    engine = db.get_bind()
    tables = inspect(engine).get_table_names()
    assert "companies" in tables
    assert "job_postings" in tables
    assert "pipeline_entries" in tables
    assert "interview_notes" in tables
    assert "pipeline_history" in tables
    assert "search_profiles" in tables
    assert "search_results" in tables


def test_create_company(db):
    company = Company(name="Acme Corp", website="https://acme.com")
    db.add(company)
    db.commit()
    assert company.id is not None
    assert company.name == "Acme Corp"


def test_create_posting_with_company(db):
    company = Company(name="Acme Corp")
    db.add(company)
    db.flush()
    posting = JobPosting(
        title="Software Engineer",
        company_id=company.id,
        location="Remote",
        remote_type="remote",
        source="linkedin",
    )
    db.add(posting)
    db.commit()
    assert posting.company.name == "Acme Corp"


def test_pipeline_entry_with_history(db):
    company = Company(name="Test Co")
    db.add(company)
    db.flush()
    posting = JobPosting(title="Engineer", company_id=company.id, source="indeed")
    db.add(posting)
    db.flush()
    entry = PipelineEntry(job_posting_id=posting.id, stage="interested", position=0)
    db.add(entry)
    db.flush()
    history = PipelineHistory(
        pipeline_entry_id=entry.id, from_stage="interested", to_stage="applying"
    )
    db.add(history)
    db.commit()
    assert len(entry.history) == 1


def test_interview_note(db):
    company = Company(name="Test Co")
    db.add(company)
    db.flush()
    posting = JobPosting(title="Engineer", company_id=company.id, source="indeed")
    db.add(posting)
    db.flush()
    entry = PipelineEntry(job_posting_id=posting.id, stage="recruiter_screen", position=0)
    db.add(entry)
    db.flush()
    note = InterviewNote(
        pipeline_entry_id=entry.id,
        round="Phone Screen",
    )
    db.add(note)
    db.commit()
    assert len(entry.interview_notes) == 1
    assert entry.interview_notes[0].round == "Phone Screen"


def test_search_profile_and_results(db):
    profile = SearchProfile(name="Remote SWE", search_term="software engineer")
    db.add(profile)
    db.flush()
    company = Company(name="Test Co")
    db.add(company)
    db.flush()
    posting = JobPosting(title="Engineer", company_id=company.id, source="linkedin")
    db.add(posting)
    db.flush()
    result = SearchResult(
        search_profile_id=profile.id, job_posting_id=posting.id, is_new=True
    )
    db.add(result)
    db.commit()
    assert len(profile.results) == 1
    assert profile.results[0].is_new is True
