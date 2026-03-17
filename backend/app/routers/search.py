import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import SearchProfile, SearchResult
from app.schemas.search import SearchProfileCreate, SearchProfileUpdate, SearchProfileRead
from app.services.search_service import run_search
from app.services.scheduler_service import schedule_profile, remove_profile_schedule

router = APIRouter(tags=["search"])


@router.get("/api/search-profiles", response_model=list[SearchProfileRead])
def list_profiles(db: Session = Depends(get_db)):
    profiles = db.query(SearchProfile).all()
    results = []
    for profile in profiles:
        profile_dict = {c.name: getattr(profile, c.name) for c in profile.__table__.columns}
        profile_dict["sources"] = json.loads(profile.sources) if profile.sources else None
        profile_dict["exclude_terms"] = json.loads(profile.exclude_terms) if profile.exclude_terms else None
        profile_dict["new_result_count"] = db.query(func.count(SearchResult.id)).filter(
            SearchResult.search_profile_id == profile.id, SearchResult.is_new == True
        ).scalar()
        results.append(SearchProfileRead.model_validate(profile_dict))
    return results


@router.post("/api/search-profiles", response_model=SearchProfileRead, status_code=201)
def create_profile(data: SearchProfileCreate, db: Session = Depends(get_db)):
    values = data.model_dump()
    if values.get("sources"):
        values["sources"] = json.dumps(values["sources"])
    if values.get("exclude_terms"):
        values["exclude_terms"] = json.dumps(values["exclude_terms"])
    profile = SearchProfile(**values)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    profile_dict = {c.name: getattr(profile, c.name) for c in profile.__table__.columns}
    profile_dict["sources"] = json.loads(profile.sources) if profile.sources else None
    profile_dict["exclude_terms"] = json.loads(profile.exclude_terms) if profile.exclude_terms else None
    profile_dict["new_result_count"] = 0  # new profile has no results yet
    return SearchProfileRead.model_validate(profile_dict)


def _profile_to_read(profile: SearchProfile, db: Session) -> SearchProfileRead:
    profile_dict = {c.name: getattr(profile, c.name) for c in profile.__table__.columns}
    profile_dict["sources"] = json.loads(profile.sources) if profile.sources else None
    profile_dict["exclude_terms"] = json.loads(profile.exclude_terms) if profile.exclude_terms else None
    profile_dict["new_result_count"] = db.query(func.count(SearchResult.id)).filter(
        SearchResult.search_profile_id == profile.id, SearchResult.is_new == True  # noqa: E712
    ).scalar()
    return SearchProfileRead.model_validate(profile_dict)


@router.put("/api/search-profiles/{profile_id}", response_model=SearchProfileRead)
def update_profile(profile_id: int, data: SearchProfileUpdate, request: Request, db: Session = Depends(get_db)):
    profile = db.get(SearchProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Search profile not found")
    values = data.model_dump(exclude_unset=True)
    if "sources" in values and values["sources"] is not None:
        values["sources"] = json.dumps(values["sources"])
    if "exclude_terms" in values and values["exclude_terms"] is not None:
        values["exclude_terms"] = json.dumps(values["exclude_terms"])
    for key, value in values.items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)

    # Update scheduler based on auto-run settings
    scheduler = getattr(request.app.state, "scheduler", None)
    if scheduler is not None and scheduler.running:
        if profile.is_auto_enabled and profile.run_interval:
            schedule_profile(scheduler, profile)
        else:
            remove_profile_schedule(scheduler, profile.id)

    return _profile_to_read(profile, db)


@router.delete("/api/search-profiles/{profile_id}", status_code=204)
def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.get(SearchProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Search profile not found")
    db.delete(profile)
    db.commit()


@router.get("/api/search-profiles/{profile_id}/postings", response_model=list)
def list_profile_postings(profile_id: int, db: Session = Depends(get_db)):
    from app.models import JobPosting
    from app.schemas.job_posting import JobPostingRead
    from sqlalchemy.orm import joinedload
    profile = db.get(SearchProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Search profile not found")
    postings = (
        db.query(JobPosting)
        .join(SearchResult, SearchResult.job_posting_id == JobPosting.id)
        .filter(SearchResult.search_profile_id == profile_id, JobPosting.status == 'unsaved')
        .options(joinedload(JobPosting.company), joinedload(JobPosting.pipeline_entry))
        .distinct()
        .all()
    )
    results = []
    for p in postings:
        data = JobPostingRead.model_validate(p)
        data.pipeline_stage = p.pipeline_entry.stage if p.pipeline_entry else None
        results.append(data)
    return results


@router.post("/api/search-profiles/{profile_id}/run")
def run_profile_search(profile_id: int, db: Session = Depends(get_db)):
    profile = db.get(SearchProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Search profile not found")
    return run_search(profile, db)


@router.post("/api/search-results/{profile_id}/mark-reviewed")
def mark_reviewed(profile_id: int, db: Session = Depends(get_db)):
    db.query(SearchResult).filter(
        SearchResult.search_profile_id == profile_id, SearchResult.is_new == True
    ).update({"is_new": False})
    db.commit()
    return {"status": "ok"}
