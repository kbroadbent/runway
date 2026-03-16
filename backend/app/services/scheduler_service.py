from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def init_scheduler(db_url: str) -> BackgroundScheduler:
    """Create an APScheduler BackgroundScheduler with a MemoryJobStore."""
    jobstores = {"default": MemoryJobStore()}
    scheduler = BackgroundScheduler(jobstores=jobstores)
    scheduler._db_url = db_url
    return scheduler


def schedule_profile(scheduler: BackgroundScheduler, profile) -> None:
    """Add or update an interval job for a profile.

    Job ID is f"search_profile_{profile.id}". Interval is profile.run_interval hours.
    If the job already exists, it will be replaced.
    """
    job_id = f"search_profile_{profile.id}"
    db_url = getattr(scheduler, "_db_url", None)

    existing = scheduler.get_job(job_id)
    if existing:
        existing.remove()

    scheduler.add_job(
        run_scheduled_search,
        trigger="interval",
        hours=profile.run_interval,
        id=job_id,
        args=[profile.id, db_url],
        replace_existing=True,
    )


def remove_profile_schedule(scheduler: BackgroundScheduler, profile_id: int) -> None:
    """Remove the scheduled job for a profile by profile_id."""
    job_id = f"search_profile_{profile_id}"
    job = scheduler.get_job(job_id)
    if job:
        job.remove()


def run_scheduled_search(profile_id: int, db_url: str) -> None:
    """Callback that creates a DB session, loads profile, and calls search_service.run_search."""
    from app.models import SearchProfile
    from app.services.search_service import run_search

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        profile = db.get(SearchProfile, profile_id)
        if profile:
            run_search(profile, db)
    finally:
        db.close()
