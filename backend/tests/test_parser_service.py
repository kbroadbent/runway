import pytest
from app.services.parser_service import parse_posting_text, fetch_and_parse_url


def test_parse_basic_posting():
    text = """
    Software Engineer
    Acme Corp
    San Francisco, CA (Remote)
    $150,000 - $200,000

    We are looking for a software engineer...
    """
    result = parse_posting_text(text)
    assert result.title == "Software Engineer"
    assert result.company_name == "Acme Corp"
    assert result.salary_min == 150000
    assert result.salary_max == 200000
    assert "remote" in (result.remote_type or "").lower()


def test_parse_posting_with_no_salary():
    text = """
    Data Scientist
    Beta Inc
    New York, NY

    Looking for a data scientist...
    """
    result = parse_posting_text(text)
    assert result.title is not None
    assert result.salary_min is None


def test_parse_returns_raw_content():
    text = "Some job posting text"
    result = parse_posting_text(text)
    assert result.raw_content == text
