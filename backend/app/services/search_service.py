import json
import math
from datetime import datetime, timezone
from jobspy import scrape_jobs
from sqlalchemy.orm import Session
from app.models import SearchProfile, SearchResult, JobPosting, Company


def run_search(profile: SearchProfile, db: Session) -> dict:
    sources = json.loads(profile.sources) if profile.sources else ["indeed"]
    exclude_terms = json.loads(profile.exclude_terms) if profile.exclude_terms else []
    df = scrape_jobs(
        site_name=sources,
        search_term=profile.search_term,
        location=profile.location,
        is_remote=profile.remote_filter == "remote",
        job_type=profile.job_type,
        results_wanted=50,
        enforce_annual_salary=True,
    )
    new_count = 0
    saved_count = 0
    total_count = len(df)
    for _, row in df.iterrows():
        url = row.get("job_url")
        title = row.get("title", "Unknown")
        company_name = row.get("company", "Unknown")

        # Salary filter: when min salary is set, require salary data that meets the threshold
        if profile.salary_min is not None:
            min_amount = _to_int(row.get("min_amount"))
            max_amount = _to_int(row.get("max_amount"))
            # No salary listed → skip
            if min_amount is None and max_amount is None:
                continue
            # Max salary is known and below threshold → skip
            if max_amount is not None and max_amount < profile.salary_min:
                continue
            # Only min_amount listed and it's below threshold → skip
            if max_amount is None and min_amount is not None and min_amount < profile.salary_min:
                continue

        # Exclude terms filter: skip if title or description contains any excluded term
        if exclude_terms:
            description = str(row.get("description") or "")
            combined = f"{title} {description}".lower()
            if any(term.lower() in combined for term in exclude_terms):
                continue

        existing = None
        if url:
            existing = db.query(JobPosting).filter(JobPosting.url == url).first()

        if not existing:
            company = db.query(Company).filter(Company.name == company_name).first()
            if company:
                existing = db.query(JobPosting).filter(
                    JobPosting.title == title, JobPosting.company_id == company.id
                ).first()

        if existing:
            # Skip postings already saved or dismissed — user has already acted on them
            if existing.status in ('saved', 'dismissed'):
                continue
            result = SearchResult(
                search_profile_id=profile.id, job_posting_id=existing.id, is_new=False
            )
            db.add(result)
            continue

        company = db.query(Company).filter(Company.name == company_name).first()
        if not company:
            company = Company(name=company_name)
            db.add(company)
            db.flush()

        remote_type = "remote" if row.get("is_remote") else None
        posting = JobPosting(
            title=title,
            company_id=company.id,
            description=_to_str(row.get("description")),
            location=_to_str(row.get("location")) or "",
            remote_type=remote_type,
            salary_min=_to_int(row.get("min_amount")),
            salary_max=_to_int(row.get("max_amount")),
            url=url,
            source=str(row.get("site", "unknown")),
            date_posted=_parse_date(row.get("date_posted")),
            status='unsaved',
        )
        db.add(posting)
        db.flush()

        result = SearchResult(
            search_profile_id=profile.id, job_posting_id=posting.id, is_new=True
        )
        db.add(result)
        new_count += 1
        saved_count += 1

    profile.last_run_at = datetime.now(timezone.utc)
    db.commit()
    return {"new_count": new_count, "saved_count": saved_count, "total_count": total_count}


def _to_int(val) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _to_str(val) -> str | None:
    if val is None:
        return None
    if isinstance(val, float) and math.isnan(val):
        return None
    return str(val)


def _parse_date(val) -> datetime | None:
    if val is None or (hasattr(val, '__class__') and val.__class__.__name__ == 'NaTType'):
        return None
    if isinstance(val, float) and math.isnan(val):
        return None
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val)
        except ValueError:
            return None
    return val
