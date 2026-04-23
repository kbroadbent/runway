import logging

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models import JobPosting, PipelineEntry
from app.services.ai_service import _llm, AIServiceError

logger = logging.getLogger(__name__)

_TERMINAL_STAGES = {"rejected", "archived", "ghosted"}

_FETCH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def get_eligible_postings(db: Session) -> list[JobPosting]:
    """Return saved postings with URLs in active pipeline stages that haven't been checked/dismissed."""
    return (
        db.query(JobPosting)
        .join(PipelineEntry)
        .filter(
            JobPosting.status == "saved",
            JobPosting.url.isnot(None),
            JobPosting.url != "",
            JobPosting.is_closed_detected == False,  # noqa: E712
            JobPosting.closed_check_dismissed == False,  # noqa: E712
            PipelineEntry.stage.notin_(_TERMINAL_STAGES),
        )
        .all()
    )


def _fetch_page_text(url: str) -> str:
    """Fetch a URL and return stripped text content."""
    with httpx.Client(follow_redirects=True, timeout=15) as client:
        response = client.get(url, headers=_FETCH_HEADERS)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for unwanted in soup(["script", "style", "nav", "header", "footer", "aside"]):
        unwanted.decompose()
    return soup.get_text(separator="\n")[:8000]


def _check_if_closed(page_text: str) -> bool:
    """Ask the AI whether the job posting page indicates the position is closed."""
    try:
        response = _llm([
            {
                "role": "system",
                "content": "You determine whether a job posting is still open. Respond with only the word 'open' or 'closed'.",
            },
            {
                "role": "user",
                "content": (
                    "Based on this job listing page content, is this job posting still open "
                    "and accepting applications? Look for signals like 'this position has been filled', "
                    "'no longer accepting applications', 'this job has expired', 404-like messages, "
                    "or any indication the role is no longer available.\n\n"
                    f"Page content:\n{page_text}"
                ),
            },
        ])
        return "closed" in response.strip().lower()
    except (AIServiceError, Exception) as exc:
        logger.warning("AI check failed: %s", exc)
        return False


def check_single_posting(posting: JobPosting, db: Session) -> None:
    """Check a single posting and update is_closed_detected if closed."""
    try:
        page_text = _fetch_page_text(posting.url)
    except Exception as exc:
        logger.warning("Failed to fetch %s: %s", posting.url, exc)
        return

    if _check_if_closed(page_text):
        posting.is_closed_detected = True
        db.commit()
        logger.info("Posting %d (%s) detected as closed", posting.id, posting.title)


def check_all_postings(db: Session) -> None:
    """Check all eligible postings for closure. Called by the scheduler."""
    postings = get_eligible_postings(db)
    logger.info("Checking %d postings for closure", len(postings))
    for posting in postings:
        check_single_posting(posting, db)
