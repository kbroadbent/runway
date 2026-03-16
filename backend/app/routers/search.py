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
    profile = SearchProfile(**values)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    profile_dict = {c.name: getattr(profile, c.name) for c in profile.__table__.columns}
    profile_dict["sources"] = json.loads(profile.sources) if profile.sources else None
    profile_dict["new_result_count"] = 0
    return SearchProfileRead.model_validate(profile_dict)


@router.put("/api/search-profiles/{profile_id}", response_model=SearchProfileRead)
def update_profile(profile_id: int, data: SearchProfileUpdate, request: Request, db: Session = Depends(get_db)):
    profile = db.get(SearchProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Search profile not found")
    values = data.model_dump(exclude_unset=True)
    if "sources" in values and values["sources"] is not None:
        values["sources"] = json.dumps(values["sources"])
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

    profile_dict = {c.name: getattr(profile, c.name) for c in profile.__table__.columns}
    profile_dict["sources"] = json.loads(profile.sources) if profile.sources else None
    profile_dict["new_result_count"] = 0
    return SearchProfileRead.model_validate(profile_dict)


@router.delete("/api/search-profiles/{profile_id}", status_code=204)
def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.get(SearchProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Search profile not found")
    db.delete(profile)
    db.commit()


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
