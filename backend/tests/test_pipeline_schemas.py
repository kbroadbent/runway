"""Tests for pipeline schema extensions: stage dates on move/update/read, custom date CRUD schemas."""

from datetime import date, datetime

import pytest
from pydantic import ValidationError


# --- PipelineMoveRequest: stage_dates field ---


def test_move_request_accepts_stage_dates():
    """PipelineMoveRequest should accept an optional stage_dates dict."""
    from app.schemas.pipeline import PipelineMoveRequest

    req = PipelineMoveRequest(
        to_stage="applied",
        stage_dates={"applied_date": date(2026, 3, 20)},
    )
    assert req.stage_dates == {"applied_date": date(2026, 3, 20)}


def test_move_request_stage_dates_defaults_to_none():
    """PipelineMoveRequest.stage_dates should default to None when not provided."""
    from app.schemas.pipeline import PipelineMoveRequest

    req = PipelineMoveRequest(to_stage="applied")
    assert req.stage_dates is None


def test_move_request_stage_dates_allows_none_values():
    """stage_dates dict values can be None to explicitly unset a date."""
    from app.schemas.pipeline import PipelineMoveRequest

    req = PipelineMoveRequest(
        to_stage="offer",
        stage_dates={"offer_date": date(2026, 4, 1), "offer_expiration_date": None},
    )
    assert req.stage_dates["offer_expiration_date"] is None


def test_move_request_stage_dates_accepts_multiple_dates():
    """stage_dates can contain multiple date fields for stages with multiple dates."""
    from app.schemas.pipeline import PipelineMoveRequest

    req = PipelineMoveRequest(
        to_stage="offer",
        stage_dates={
            "offer_date": date(2026, 4, 1),
            "offer_expiration_date": date(2026, 4, 15),
        },
    )
    assert len(req.stage_dates) == 2


# --- PipelineEntryUpdate: stage-linked date fields ---


STAGE_DATE_FIELD_NAMES = [
    "applied_date",
    "recruiter_screen_date",
    "tech_screen_date",
    "onsite_date",
    "offer_date",
    "offer_expiration_date",
]


@pytest.mark.parametrize("field_name", STAGE_DATE_FIELD_NAMES)
def test_entry_update_accepts_stage_date_field(field_name):
    """PipelineEntryUpdate should accept each stage-linked date field."""
    from app.schemas.pipeline import PipelineEntryUpdate

    update = PipelineEntryUpdate(**{field_name: date(2026, 3, 20)})
    assert getattr(update, field_name) == date(2026, 3, 20)


@pytest.mark.parametrize("field_name", STAGE_DATE_FIELD_NAMES)
def test_entry_update_stage_date_fields_default_to_none(field_name):
    """Stage-linked date fields should default to None."""
    from app.schemas.pipeline import PipelineEntryUpdate

    update = PipelineEntryUpdate()
    assert getattr(update, field_name) is None


def test_entry_update_preserves_existing_fields():
    """Adding date fields should not break existing next_action fields."""
    from app.schemas.pipeline import PipelineEntryUpdate

    update = PipelineEntryUpdate(
        next_action="Follow up",
        next_action_date=datetime(2026, 3, 25, 10, 0),
        applied_date=date(2026, 3, 20),
    )
    assert update.next_action == "Follow up"
    assert update.applied_date == date(2026, 3, 20)


# --- PipelineEntryRead: stage-linked date fields ---


@pytest.mark.parametrize("field_name", STAGE_DATE_FIELD_NAMES)
def test_entry_read_includes_stage_date_field(field_name):
    """PipelineEntryRead should include each stage-linked date field."""
    from app.schemas.pipeline import PipelineEntryRead

    fields = PipelineEntryRead.model_fields
    assert field_name in fields, f"{field_name} missing from PipelineEntryRead"


@pytest.mark.parametrize("field_name", STAGE_DATE_FIELD_NAMES)
def test_entry_read_stage_date_fields_are_optional(field_name):
    """Stage-linked date fields on PipelineEntryRead should be optional (None allowed)."""
    from app.schemas.pipeline import PipelineEntryRead

    field_info = PipelineEntryRead.model_fields[field_name]
    # Check that the field's default is None (optional)
    assert field_info.default is None, f"{field_name} should default to None"


# --- CustomDateCreate schema ---


def test_custom_date_create_valid():
    """CustomDateCreate should accept a label and date."""
    from app.schemas.pipeline import CustomDateCreate

    cd = CustomDateCreate(label="Follow-up call", date=date(2026, 4, 1))
    assert cd.label == "Follow-up call"
    assert cd.date == date(2026, 4, 1)


def test_custom_date_create_rejects_empty_label():
    """CustomDateCreate should reject an empty label."""
    from app.schemas.pipeline import CustomDateCreate

    with pytest.raises(ValidationError):
        CustomDateCreate(label="", date=date(2026, 4, 1))


def test_custom_date_create_rejects_label_over_100_chars():
    """CustomDateCreate should reject labels longer than 100 characters."""
    from app.schemas.pipeline import CustomDateCreate

    with pytest.raises(ValidationError):
        CustomDateCreate(label="x" * 101, date=date(2026, 4, 1))


def test_custom_date_create_accepts_label_at_100_chars():
    """CustomDateCreate should accept a label of exactly 100 characters."""
    from app.schemas.pipeline import CustomDateCreate

    cd = CustomDateCreate(label="x" * 100, date=date(2026, 4, 1))
    assert len(cd.label) == 100


def test_custom_date_create_requires_label():
    """CustomDateCreate should require a label field."""
    from app.schemas.pipeline import CustomDateCreate

    with pytest.raises(ValidationError):
        CustomDateCreate(date=date(2026, 4, 1))


def test_custom_date_create_requires_date():
    """CustomDateCreate should require a date field."""
    from app.schemas.pipeline import CustomDateCreate

    with pytest.raises(ValidationError):
        CustomDateCreate(label="Test")


# --- CustomDateUpdate schema ---


def test_custom_date_update_accepts_label_only():
    """CustomDateUpdate should accept just a label."""
    from app.schemas.pipeline import CustomDateUpdate

    cd = CustomDateUpdate(label="New label")
    assert cd.label == "New label"
    assert cd.date is None


def test_custom_date_update_accepts_date_only():
    """CustomDateUpdate should accept just a date."""
    from app.schemas.pipeline import CustomDateUpdate

    cd = CustomDateUpdate(date=date(2026, 5, 1))
    assert cd.date == date(2026, 5, 1)
    assert cd.label is None


def test_custom_date_update_accepts_both():
    """CustomDateUpdate should accept both label and date."""
    from app.schemas.pipeline import CustomDateUpdate

    cd = CustomDateUpdate(label="Updated", date=date(2026, 5, 1))
    assert cd.label == "Updated"
    assert cd.date == date(2026, 5, 1)


def test_custom_date_update_rejects_empty_label():
    """CustomDateUpdate should reject an empty label when provided."""
    from app.schemas.pipeline import CustomDateUpdate

    with pytest.raises(ValidationError):
        CustomDateUpdate(label="")


def test_custom_date_update_rejects_label_over_100_chars():
    """CustomDateUpdate should reject labels longer than 100 characters."""
    from app.schemas.pipeline import CustomDateUpdate

    with pytest.raises(ValidationError):
        CustomDateUpdate(label="x" * 101)


# --- CustomDateRead schema ---


def test_custom_date_read_has_expected_fields():
    """CustomDateRead should have id, label, date, and created_at fields."""
    from app.schemas.pipeline import CustomDateRead

    fields = CustomDateRead.model_fields
    assert "id" in fields
    assert "label" in fields
    assert "date" in fields
    assert "created_at" in fields


def test_custom_date_read_from_attributes_enabled():
    """CustomDateRead should have from_attributes=True for ORM compatibility."""
    from app.schemas.pipeline import CustomDateRead

    assert CustomDateRead.model_config.get("from_attributes") is True


# --- PipelineEntryRead: custom_dates relationship ---


def test_entry_read_includes_custom_dates_field():
    """PipelineEntryRead should include a custom_dates list field."""
    from app.schemas.pipeline import PipelineEntryRead

    fields = PipelineEntryRead.model_fields
    assert "custom_dates" in fields, "custom_dates missing from PipelineEntryRead"
