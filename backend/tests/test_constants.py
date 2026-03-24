from app.constants import STAGES, VALID_STAGES


def test_stage_groups_maps_every_stage():
    """STAGE_GROUPS must have an entry for every stage in STAGES."""
    from app.constants import STAGE_GROUPS

    for stage in STAGES:
        assert stage in STAGE_GROUPS, f"Stage '{stage}' missing from STAGE_GROUPS"


def test_stage_groups_contains_no_extra_keys():
    """STAGE_GROUPS should not contain keys that aren't in STAGES."""
    from app.constants import STAGE_GROUPS

    for key in STAGE_GROUPS:
        assert key in VALID_STAGES, f"STAGE_GROUPS key '{key}' is not a valid stage"


def test_stage_groups_values_are_display_strings():
    """Each STAGE_GROUPS value should be a non-empty string (display label)."""
    from app.constants import STAGE_GROUPS

    for stage, group in STAGE_GROUPS.items():
        assert isinstance(group, str) and len(group) > 0, (
            f"STAGE_GROUPS['{stage}'] should be a non-empty string, got {group!r}"
        )


def test_stage_groups_merges_scheduled_and_completed():
    """Scheduled and completed sub-stages should map to the same group."""
    from app.constants import STAGE_GROUPS

    assert STAGE_GROUPS["recruiter_screen_scheduled"] == STAGE_GROUPS["recruiter_screen_completed"]
    assert STAGE_GROUPS["tech_screen_scheduled"] == STAGE_GROUPS["tech_screen_completed"]
    assert STAGE_GROUPS["onsite_scheduled"] == STAGE_GROUPS["onsite_completed"]


def test_stage_group_order_exists_and_is_list():
    """STAGE_GROUP_ORDER should be a list."""
    from app.constants import STAGE_GROUP_ORDER

    assert isinstance(STAGE_GROUP_ORDER, list)


def test_stage_group_order_contains_all_unique_groups():
    """STAGE_GROUP_ORDER should contain every unique group value exactly once."""
    from app.constants import STAGE_GROUPS, STAGE_GROUP_ORDER

    unique_groups = set(STAGE_GROUPS.values())
    assert set(STAGE_GROUP_ORDER) == unique_groups
    assert len(STAGE_GROUP_ORDER) == len(unique_groups)


def test_stage_group_order_has_nine_groups():
    """There should be exactly 9 display groups."""
    from app.constants import STAGE_GROUP_ORDER

    assert len(STAGE_GROUP_ORDER) == 9


def test_stage_group_order_preserves_pipeline_order():
    """Groups should appear in pipeline progression order."""
    from app.constants import STAGE_GROUP_ORDER

    expected = [
        "Interested",
        "Applying",
        "Applied",
        "Recruiter Screen",
        "Tech Screen",
        "Onsite",
        "Offer",
        "Rejected",
        "Archived",
    ]
    assert STAGE_GROUP_ORDER == expected
