from app.constants import VALID_STAGES


def test_stage_date_fields_exists_and_is_dict():
    """STAGE_DATE_FIELDS should be a dict."""
    from app.constants import STAGE_DATE_FIELDS

    assert isinstance(STAGE_DATE_FIELDS, dict)


def test_stage_date_fields_keys_are_valid_stages():
    """Every key in STAGE_DATE_FIELDS must be a valid stage."""
    from app.constants import STAGE_DATE_FIELDS

    for key in STAGE_DATE_FIELDS:
        assert key in VALID_STAGES, f"STAGE_DATE_FIELDS key '{key}' is not a valid stage"


def test_stage_date_fields_values_are_lists_of_tuples():
    """Each value should be a list of (field_name, display_label) tuples."""
    from app.constants import STAGE_DATE_FIELDS

    for stage, fields in STAGE_DATE_FIELDS.items():
        assert isinstance(fields, list), f"STAGE_DATE_FIELDS['{stage}'] should be a list"
        for item in fields:
            assert isinstance(item, tuple) and len(item) == 2, (
                f"STAGE_DATE_FIELDS['{stage}'] items should be 2-tuples, got {item!r}"
            )
            field_name, label = item
            assert isinstance(field_name, str) and len(field_name) > 0, (
                f"Field name in STAGE_DATE_FIELDS['{stage}'] should be a non-empty string"
            )
            assert isinstance(label, str) and len(label) > 0, (
                f"Label in STAGE_DATE_FIELDS['{stage}'] should be a non-empty string"
            )


def test_stage_date_fields_has_expected_stages():
    """STAGE_DATE_FIELDS should contain entries for applied, scheduled stages, and offer."""
    from app.constants import STAGE_DATE_FIELDS

    expected_keys = {
        "applied",
        "recruiter_screen_scheduled",
        "manager_screen_scheduled",
        "tech_screen_scheduled",
        "onsite_scheduled",
        "offer_verbal",
        "offer_written",
    }
    assert set(STAGE_DATE_FIELDS.keys()) == expected_keys


def test_applied_has_applied_date():
    """The applied stage should map to an applied_date field."""
    from app.constants import STAGE_DATE_FIELDS

    fields = STAGE_DATE_FIELDS["applied"]
    assert len(fields) == 1
    assert fields[0] == ("applied_date", "Applied Date")


def test_recruiter_screen_scheduled_has_date():
    """The recruiter_screen_scheduled stage should map to a recruiter_screen_date field."""
    from app.constants import STAGE_DATE_FIELDS

    fields = STAGE_DATE_FIELDS["recruiter_screen_scheduled"]
    assert len(fields) == 1
    assert fields[0] == ("recruiter_screen_date", "Recruiter Screen Date")


def test_tech_screen_scheduled_has_date():
    """The tech_screen_scheduled stage should map to a tech_screen_date field."""
    from app.constants import STAGE_DATE_FIELDS

    fields = STAGE_DATE_FIELDS["tech_screen_scheduled"]
    assert len(fields) == 1
    assert fields[0] == ("tech_screen_date", "Tech Screen Date")


def test_onsite_scheduled_has_date():
    """The onsite_scheduled stage should map to an onsite_date field."""
    from app.constants import STAGE_DATE_FIELDS

    fields = STAGE_DATE_FIELDS["onsite_scheduled"]
    assert len(fields) == 1
    assert fields[0] == ("onsite_date", "Onsite Date")


def test_offer_verbal_has_offer_date():
    """The offer_verbal stage should have offer_date."""
    from app.constants import STAGE_DATE_FIELDS

    fields = STAGE_DATE_FIELDS["offer_verbal"]
    assert len(fields) == 1
    assert fields[0] == ("offer_date", "Offer Date")


def test_offer_written_has_expiration_date():
    """The offer_written stage should have offer_expiration_date."""
    from app.constants import STAGE_DATE_FIELDS

    fields = STAGE_DATE_FIELDS["offer_written"]
    assert len(fields) == 1
    assert fields[0] == ("offer_expiration_date", "Offer Expiration Date")


def test_stage_date_fields_field_names_are_unique():
    """All field names across all stages should be unique."""
    from app.constants import STAGE_DATE_FIELDS

    all_field_names = [
        field_name
        for fields in STAGE_DATE_FIELDS.values()
        for field_name, _ in fields
    ]
    assert len(all_field_names) == len(set(all_field_names)), (
        f"Duplicate field names found: {all_field_names}"
    )


def test_stage_date_fields_type_annotation():
    """STAGE_DATE_FIELDS should be typed as dict[str, list[tuple[str, str]]]."""
    from app.constants import STAGE_DATE_FIELDS

    assert isinstance(STAGE_DATE_FIELDS, dict)
    for stage, fields in STAGE_DATE_FIELDS.items():
        assert isinstance(stage, str)
        assert isinstance(fields, list)
        for field_name, label in fields:
            assert isinstance(field_name, str)
            assert isinstance(label, str)
