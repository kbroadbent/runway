"""Tests for dashboard Pydantic schemas: ActionItemRead, InterviewItemRead, DashboardResponse."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.dashboard import ActionItemRead, DashboardResponse


class TestActionItemRead:
    def test_valid_action_item_with_all_fields(self):
        item = ActionItemRead(
            pipeline_entry_id=1,
            job_title="Software Engineer",
            company_name="Acme Corp",
            type="next_action",
            description="Submit application",
            date="2026-03-25",
            is_overdue=False,
        )
        assert item.pipeline_entry_id == 1
        assert item.job_title == "Software Engineer"
        assert item.company_name == "Acme Corp"
        assert item.type == "next_action"
        assert item.description == "Submit application"
        assert item.date == "2026-03-25"
        assert item.is_overdue is False

    def test_valid_action_item_with_nullable_fields(self):
        item = ActionItemRead(
            pipeline_entry_id=2,
            job_title="Backend Dev",
            company_name=None,
            type="interview",
            description="Phone screen tomorrow",
            date=None,
            is_overdue=False,
        )
        assert item.company_name is None
        assert item.date is None

    def test_overdue_action_item(self):
        item = ActionItemRead(
            pipeline_entry_id=3,
            job_title="SRE",
            company_name="BigCo",
            type="next_action",
            description="Follow up email",
            date="2026-03-20",
            is_overdue=True,
        )
        assert item.is_overdue is True

    def test_action_item_requires_pipeline_entry_id(self):
        with pytest.raises(ValidationError):
            ActionItemRead(
                job_title="Engineer",
                company_name="Co",
                type="next_action",
                description="Do thing",
                date=None,
                is_overdue=False,
            )

    def test_action_item_requires_job_title(self):
        with pytest.raises(ValidationError):
            ActionItemRead(
                pipeline_entry_id=1,
                company_name="Co",
                type="next_action",
                description="Do thing",
                date=None,
                is_overdue=False,
            )

    def test_action_item_requires_type(self):
        with pytest.raises(ValidationError):
            ActionItemRead(
                pipeline_entry_id=1,
                job_title="Engineer",
                company_name="Co",
                description="Do thing",
                date=None,
                is_overdue=False,
            )

    def test_action_item_requires_description(self):
        with pytest.raises(ValidationError):
            ActionItemRead(
                pipeline_entry_id=1,
                job_title="Engineer",
                company_name="Co",
                type="next_action",
                date=None,
                is_overdue=False,
            )

    def test_action_item_requires_is_overdue(self):
        with pytest.raises(ValidationError):
            ActionItemRead(
                pipeline_entry_id=1,
                job_title="Engineer",
                company_name="Co",
                type="next_action",
                description="Do thing",
                date=None,
            )

    def test_action_item_serializes_to_dict(self):
        item = ActionItemRead(
            pipeline_entry_id=1,
            job_title="Engineer",
            company_name="Acme",
            type="next_action",
            description="Apply",
            date="2026-04-01",
            is_overdue=False,
        )
        data = item.model_dump()
        assert data == {
            "pipeline_entry_id": 1,
            "job_title": "Engineer",
            "company_name": "Acme",
            "type": "next_action",
            "description": "Apply",
            "date": "2026-04-01",
            "is_overdue": False,
        }


class TestDashboardResponse:
    def test_valid_dashboard_response_with_empty_lists(self):
        resp = DashboardResponse(
            lane_counts={"Interested": 3, "Applied": 1},
            action_items=[],
        )
        assert resp.lane_counts == {"Interested": 3, "Applied": 1}
        assert resp.action_items == []

    def test_dashboard_response_with_action_items(self):
        action = ActionItemRead(
            pipeline_entry_id=1,
            job_title="Engineer",
            company_name="Acme",
            type="next_action",
            description="Follow up",
            date=None,
            is_overdue=False,
        )
        resp = DashboardResponse(
            lane_counts={"Interested": 2},
            action_items=[action],
        )
        assert len(resp.action_items) == 1
        assert resp.action_items[0].job_title == "Engineer"

    def test_dashboard_response_requires_lane_counts(self):
        with pytest.raises(ValidationError):
            DashboardResponse(action_items=[])

    def test_dashboard_response_requires_action_items(self):
        with pytest.raises(ValidationError):
            DashboardResponse(lane_counts={"Interested": 1})

    def test_dashboard_response_lane_counts_is_string_to_int_dict(self):
        resp = DashboardResponse(
            lane_counts={"Interested": 5, "Applying": 0, "Offer": 1},
            action_items=[],
        )
        for key, val in resp.lane_counts.items():
            assert isinstance(key, str)
            assert isinstance(val, int)

    def test_dashboard_response_serializes_to_dict(self):
        resp = DashboardResponse(
            lane_counts={"Applied": 2},
            action_items=[
                ActionItemRead(
                    pipeline_entry_id=10,
                    job_title="Dev",
                    company_name=None,
                    type="interview",
                    description="Prep for onsite",
                    date="2026-04-05",
                    is_overdue=False,
                ),
            ],
        )
        data = resp.model_dump()
        assert data["lane_counts"] == {"Applied": 2}
        assert len(data["action_items"]) == 1
        assert data["action_items"][0]["pipeline_entry_id"] == 10
