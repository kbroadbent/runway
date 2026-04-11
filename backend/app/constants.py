STAGES = [
    "interested",
    "applying",
    "applied",
    "recruiter_screen_scheduled",
    "recruiter_screen_completed",
    "manager_screen_scheduled",
    "manager_screen_completed",
    "tech_screen_scheduled",
    "tech_screen_completed",
    "onsite_scheduled",
    "onsite_completed",
    "offer",
    "rejected",
    "withdrawn",
    "archived",
]

VALID_STAGES = set(STAGES)

STAGE_GROUPS = {
    "interested": "Interested",
    "applying": "Applying",
    "applied": "Applied",
    "recruiter_screen_scheduled": "Recruiter Screen",
    "recruiter_screen_completed": "Recruiter Screen",
    "manager_screen_scheduled": "Manager Screen",
    "manager_screen_completed": "Manager Screen",
    "tech_screen_scheduled": "Tech Screen",
    "tech_screen_completed": "Tech Screen",
    "onsite_scheduled": "Onsite",
    "onsite_completed": "Onsite",
    "offer": "Offer",
    "rejected": "Rejected",
    "withdrawn": "Withdrawn",
    "archived": "Archived",
}

STAGE_DATE_FIELDS: dict[str, list[tuple[str, str]]] = {
    "applied": [("applied_date", "Applied Date")],
    "recruiter_screen_scheduled": [("recruiter_screen_date", "Recruiter Screen Date")],
    "manager_screen_scheduled": [("manager_screen_date", "Manager Screen Date")],
    "tech_screen_scheduled": [("tech_screen_date", "Tech Screen Date")],
    "onsite_scheduled": [("onsite_date", "Onsite Date")],
    "offer": [("offer_date", "Offer Date"), ("offer_expiration_date", "Offer Expiration Date")],
}

STAGE_GROUP_ORDER = [
    "Interested",
    "Applying",
    "Applied",
    "Recruiter Screen",
    "Manager Screen",
    "Tech Screen",
    "Onsite",
    "Offer",
    "Rejected",
    "Withdrawn",
    "Archived",
]
