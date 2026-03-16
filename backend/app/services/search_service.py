import json
from datetime import datetime
from jobspy import scrape_jobs
from sqlalchemy.orm import Session
from app.models import SearchProfile, SearchResult, JobPosting, Company


def run_search(profile: SearchProfile, db: Session) -> dict:
    sources = json.loads(profile.sources) if profile.sources else ["indeed"]
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
    for _, row in df.iterrows():
        url = row.get("job_url")
        title = row.get("title", "Unknown")
        company_name = row.get("company", "Unknown")

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
            description=row.get("description"),
            location=str(row.get("location", "")),
            remote_type=remote_type,
            salary_min=int(row["min_amount"]) if row.get("min_amount") else None,
            salary_max=int(row["max_amount"]) if row.get("max_amount") else None,
            url=url,
            source=str(row.get("site", "unknown")),
            date_posted=_parse_date(row.get("date_posted")),
        )
        db.add(posting)
        db.flush()

        result = SearchResult(
            search_profile_id=profile.id, job_posting_id=posting.id, is_new=True
        )
        db.add(result)
        new_count += 1

    profile.last_run_at = datetime.utcnow()
    db.commit()
    return {"new_count": new_count, "total_count": total_count}


def _parse_date(val) -> datetime | None:
    if val is None or (hasattr(val, '__class__') and val.__class__.__name__ == 'NaTType'):
        return None
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val)
        except ValueError:
            return None
    return val
