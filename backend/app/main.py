import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import companies, postings, pipeline, search
from app.services.scheduler_service import init_scheduler, schedule_profile
from app.database import DATABASE_URL, SessionLocal
from app.models import SearchProfile, JobPosting, PipelineEntry, PipelineHistory


@asynccontextmanager
async def lifespan(app):
    scheduler = init_scheduler(DATABASE_URL)
    # Only start the scheduler in production (not during tests)
    if os.getenv("SCHEDULER_ENABLED", "false").lower() == "true":
        scheduler.start()
        # Restore auto-enabled profiles from the database
        db = SessionLocal()
        try:
            profiles = db.query(SearchProfile).filter(
                SearchProfile.is_auto_enabled == True,  # noqa: E712
                SearchProfile.run_interval != None,  # noqa: E711
            ).all()
            for profile in profiles:
                schedule_profile(scheduler, profile)
        finally:
            db.close()
    # Backfill pipeline entries for any saved postings that don't have one
    db = SessionLocal()
    try:
        orphans = db.query(JobPosting).outerjoin(PipelineEntry).filter(
            JobPosting.status == 'saved',
            PipelineEntry.id == None,  # noqa: E711
        ).all()
        for posting in orphans:
            entry = PipelineEntry(job_posting_id=posting.id, stage="interested", position=0)
            db.add(entry)
            db.flush()
            db.add(PipelineHistory(
                pipeline_entry_id=entry.id, from_stage=None, to_stage="interested", event_type="stage_change"
            ))
        if orphans:
            db.commit()
    finally:
        db.close()

    app.state.scheduler = scheduler
    yield
    if scheduler.running:
        scheduler.shutdown()


app = FastAPI(title="Runway", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(companies.router)
app.include_router(postings.router)
app.include_router(pipeline.router)
app.include_router(search.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
