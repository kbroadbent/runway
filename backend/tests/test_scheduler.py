import pytest
from unittest.mock import patch, MagicMock
from app.services.scheduler_service import init_scheduler, schedule_profile, remove_profile_schedule


def test_init_scheduler():
    scheduler = init_scheduler("sqlite:///:memory:")
    assert scheduler is not None
    assert scheduler.running is False


def test_schedule_profile():
    scheduler = init_scheduler("sqlite:///:memory:")
    scheduler.start()
    profile = MagicMock(id=1, run_interval=24, is_auto_enabled=True)
    schedule_profile(scheduler, profile)
    job = scheduler.get_job(f"search_profile_{profile.id}")
    assert job is not None
    scheduler.shutdown()


def test_remove_profile_schedule():
    scheduler = init_scheduler("sqlite:///:memory:")
    scheduler.start()
    profile = MagicMock(id=1, run_interval=24, is_auto_enabled=True)
    schedule_profile(scheduler, profile)
    remove_profile_schedule(scheduler, profile.id)
    job = scheduler.get_job(f"search_profile_{profile.id}")
    assert job is None
    scheduler.shutdown()
