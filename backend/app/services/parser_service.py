import re
import httpx
from bs4 import BeautifulSoup
from app.schemas.job_posting import ImportPreview
from app.services import ai_service
from app.services.ai_service import AIServiceError


# --- salary patterns ---
_SALARY_RANGE_RE = re.compile(
    r"\$\s*([\d,]+(?:\.\d+)?[kK]?)\s*[-–—to]+\s*\$?\s*([\d,]+(?:\.\d+)?[kK]?)",
    re.IGNORECASE,
)
_SALARY_SINGLE_RE = re.compile(
    r"\$\s*([\d,]+(?:\.\d+)?[kK]?)(?:/yr|/year|per year)?",
    re.IGNORECASE,
)

# --- remote indicators ---
_REMOTE_RE = re.compile(r"\b(remote|hybrid|on.?site|in.?office)\b", re.IGNORECASE)


def _parse_salary_value(raw: str) -> int:
    """Convert a salary string like '150,000' or '150k' to an int."""
    raw = raw.replace(",", "").strip()
    multiplier = 1
    if raw.lower().endswith("k"):
        multiplier = 1000
        raw = raw[:-1]
    return int(float(raw) * multiplier)


def _extract_salary(text: str) -> tuple[int | None, int | None]:
    m = _SALARY_RANGE_RE.search(text)
    if m:
        lo = _parse_salary_value(m.group(1))
        hi = _parse_salary_value(m.group(2))
        return lo, hi
    m = _SALARY_SINGLE_RE.search(text)
    if m:
        val = _parse_salary_value(m.group(1))
        return val, None
    return None, None


_REMOTE_NORMALIZE = {
    "remote": "remote",
    "hybrid": "hybrid",
}


def _extract_remote_type(text: str) -> str | None:
    m = _REMOTE_RE.search(text)
    if m:
        raw = m.group(1).lower()
        if raw in _REMOTE_NORMALIZE:
            return _REMOTE_NORMALIZE[raw]
        # on-site, on site, in-office, in office → onsite
        return "onsite"
    return None


def parse_posting_text(text: str) -> ImportPreview:
    """Parse raw job posting text and return an ImportPreview with extracted fields."""
    try:
        return ai_service.extract_job_posting(text)
    except AIServiceError:
        pass

    salary_min, salary_max = _extract_salary(text)
    remote_type = _extract_remote_type(text)

    # Extract non-empty lines for title / company fallback
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    title: str | None = None
    company_name: str | None = None
    location: str | None = None

    # Heuristic: first line is title, second is company, third may be location
    if lines:
        title = lines[0]
    if len(lines) > 1:
        company_name = lines[1]
    if len(lines) > 2:
        # Only treat as location if it looks like a city/state or contains location keywords
        candidate = lines[2]
        if re.search(r",\s*[A-Z]{2}|remote|hybrid|on.?site", candidate, re.IGNORECASE):
            location = candidate

    # Build description from remaining lines (after title/company/location)
    desc_start = 3 if location else 2
    description_lines = lines[desc_start:]
    description = "\n".join(description_lines) if description_lines else None

    return ImportPreview(
        title=title,
        company_name=company_name,
        location=location,
        remote_type=remote_type,
        salary_min=salary_min,
        salary_max=salary_max,
        description=description,
        raw_content=text,
    )


def fetch_and_parse_url(url: str) -> ImportPreview:
    """Fetch a URL, extract text, and parse it as a job posting."""
    with httpx.Client(follow_redirects=True, timeout=15) as client:
        response = client.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        response.raise_for_status()
        html = response.text

    soup = BeautifulSoup(html, "html.parser")

    # Try structured data from meta tags first
    og_title = None
    og_company = None
    for tag in soup.find_all("meta"):
        prop = tag.get("property", "") or tag.get("name", "")
        content = tag.get("content", "")
        if prop == "og:title" and content:
            og_title = content
        elif prop in ("og:site_name", "author") and content:
            og_company = og_company or content

    # Extract plain text
    for unwanted in soup(["script", "style", "nav", "header", "footer", "aside"]):
        unwanted.decompose()

    page_text = soup.get_text(separator="\n")

    try:
        preview = ai_service.extract_job_posting(page_text)
        preview.url = url
        return preview
    except AIServiceError:
        pass

    preview = parse_posting_text(page_text)
    preview.url = url

    # Override with structured meta data when available
    if og_title:
        preview.title = og_title
    if og_company:
        preview.company_name = og_company

    return preview
