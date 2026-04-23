from unittest.mock import patch
from app.models import JobPosting, PipelineEntry, PipelineHistory
from app.services.posting_check_service import get_eligible_postings, check_single_posting


def _create_eligible_posting(db_session, title="SWE", url="https://example.com/job"):
    """Create a saved posting with a pipeline entry in an active stage."""
    posting = JobPosting(
        title=title, url=url, source="manual", status="saved",
        company_name="TestCo",
    )
    db_session.add(posting)
    db_session.flush()
    entry = PipelineEntry(job_posting_id=posting.id, stage="interested", position=0)
    db_session.add(entry)
    db_session.flush()
    db_session.add(PipelineHistory(
        pipeline_entry_id=entry.id, from_stage=None, to_stage="interested", event_type="stage_change"
    ))
    db_session.commit()
    return posting


def test_get_eligible_postings_returns_active_saved_with_url(db_session):
    posting = _create_eligible_posting(db_session)
    eligible = get_eligible_postings(db_session)
    assert len(eligible) == 1
    assert eligible[0].id == posting.id


def test_get_eligible_postings_excludes_no_url(db_session):
    _create_eligible_posting(db_session, url=None)
    eligible = get_eligible_postings(db_session)
    assert len(eligible) == 0


def test_get_eligible_postings_excludes_dismissed(db_session):
    posting = _create_eligible_posting(db_session)
    posting.closed_check_dismissed = True
    db_session.commit()
    eligible = get_eligible_postings(db_session)
    assert len(eligible) == 0


def test_get_eligible_postings_excludes_already_closed(db_session):
    posting = _create_eligible_posting(db_session)
    posting.is_closed_detected = True
    db_session.commit()
    eligible = get_eligible_postings(db_session)
    assert len(eligible) == 0


def test_get_eligible_postings_excludes_terminal_stages(db_session):
    posting = _create_eligible_posting(db_session)
    posting.pipeline_entry.stage = "rejected"
    db_session.commit()
    eligible = get_eligible_postings(db_session)
    assert len(eligible) == 0


def test_get_eligible_postings_excludes_unsaved(db_session):
    posting = _create_eligible_posting(db_session)
    posting.status = "dismissed"
    db_session.commit()
    eligible = get_eligible_postings(db_session)
    assert len(eligible) == 0


@patch("app.services.posting_check_service._fetch_page_text")
@patch("app.services.posting_check_service._check_if_closed")
def test_check_single_posting_marks_closed(mock_check, mock_fetch, db_session):
    posting = _create_eligible_posting(db_session)
    mock_fetch.return_value = "This position has been filled."
    mock_check.return_value = True

    check_single_posting(posting, db_session)

    db_session.refresh(posting)
    assert posting.is_closed_detected is True


@patch("app.services.posting_check_service._fetch_page_text")
@patch("app.services.posting_check_service._check_if_closed")
def test_check_single_posting_leaves_open(mock_check, mock_fetch, db_session):
    posting = _create_eligible_posting(db_session)
    mock_fetch.return_value = "Apply now for this exciting role!"
    mock_check.return_value = False

    check_single_posting(posting, db_session)

    db_session.refresh(posting)
    assert posting.is_closed_detected is False


@patch("app.services.posting_check_service._fetch_page_text")
def test_check_single_posting_skips_on_fetch_error(mock_fetch, db_session):
    posting = _create_eligible_posting(db_session)
    mock_fetch.side_effect = Exception("Connection timeout")

    check_single_posting(posting, db_session)

    db_session.refresh(posting)
    assert posting.is_closed_detected is False


def test_get_eligible_postings_excludes_ghosted_stage(db_session):
    """Postings with pipeline entries in ghosted stage should not be eligible for checks."""
    posting = _create_eligible_posting(db_session)
    posting.pipeline_entry.stage = "ghosted"
    db_session.commit()
    eligible = get_eligible_postings(db_session)
    assert len(eligible) == 0
