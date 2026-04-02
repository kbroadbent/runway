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
    total_count = len(df)

    # Reset new flags from previous run so badge reflects this run only
    db.query(SearchResult).filter(
        SearchResult.search_profile_id == profile.id,
        SearchResult.is_new.is_(True),
    ).update({"is_new": False}, synchronize_session=False)
    db.flush()

    # Build seen sets from raw scrape (before filters) for age-out tracking
    seen_urls: set[str] = {str(row["job_url"]) for _, row in df.iterrows() if row.get("job_url")}
    seen_title_company: set[tuple[str, str]] = {
        (str(row.get("title") or "").lower(), (_to_str(row.get("company")) or "").lower())
        for _, row in df.iterrows()
        if row.get("title") and row.get("company")
    }

    for _, row in df.iterrows():
        url = row.get("job_url")
        title = row.get("title", "Unknown")
        company_name = _to_str(row.get("company")) or "Unknown"

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
            existing_result = db.query(SearchResult).filter(
                SearchResult.search_profile_id == profile.id,
                SearchResult.job_posting_id == existing.id,
            ).first()
            if existing_result:
                existing_result.run_date = datetime.now(timezone.utc)
            else:
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

        # Re-check with resolved company.id — the earlier check may have been skipped
        # if the company didn't exist yet (e.g. first time seeing this company in this run)
        existing = db.query(JobPosting).filter(
            JobPosting.title == title, JobPosting.company_id == company.id
        ).first()
        if existing:
            if existing.status not in ('saved', 'dismissed'):
                existing_result = db.query(SearchResult).filter(
                    SearchResult.search_profile_id == profile.id,
                    SearchResult.job_posting_id == existing.id,
                ).first()
                if existing_result:
                    existing_result.run_date = datetime.now(timezone.utc)
                else:
                    result = SearchResult(
                        search_profile_id=profile.id, job_posting_id=existing.id, is_new=False
                    )
                    db.add(result)
            continue

        remote_type = "remote" if row.get("is_remote") else None
        posting = JobPosting(
            title=title,
            company_id=company.id,
            company_name=company_name,
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

    # Age-out: update consecutive_misses for unsaved postings linked to this profile
    AGE_OUT_THRESHOLD = 5
    linked_unsaved = (
        db.query(JobPosting)
        .join(SearchResult, SearchResult.job_posting_id == JobPosting.id)
        .filter(SearchResult.search_profile_id == profile.id, JobPosting.status == 'unsaved')
        .distinct()
        .all()
    )
    for posting in linked_unsaved:
        still_seen = (
            (posting.url and posting.url in seen_urls)
            or ((posting.title or "").lower(), (posting.company_name or "").lower()) in seen_title_company
        )
        if still_seen:
            posting.consecutive_misses = 0
        else:
            posting.consecutive_misses += 1
            if posting.consecutive_misses >= AGE_OUT_THRESHOLD:
                _age_out_posting(posting, profile.id, db)

    profile.last_run_at = datetime.now(timezone.utc)
    db.commit()
    return {"new_count": new_count, "total_count": total_count}


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


def _age_out_posting(posting: JobPosting, profile_id: int, db: Session) -> None:
    """Remove posting from this profile's search queue.
    Deletes the posting entirely if no other profile holds an unsaved link to it."""
    # Remove all SearchResult links for this profile
    db.query(SearchResult).filter(
        SearchResult.job_posting_id == posting.id,
        SearchResult.search_profile_id == profile_id,
    ).delete(synchronize_session=False)

    # Check if any other profile still has an unsaved link
    other_link = (
        db.query(SearchResult)
        .join(JobPosting, JobPosting.id == SearchResult.job_posting_id)
        .filter(
            SearchResult.job_posting_id == posting.id,
            SearchResult.search_profile_id != profile_id,
            JobPosting.status == 'unsaved',
        )
        .first()
    )
    if other_link is None:
        db.delete(posting)
