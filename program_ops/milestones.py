"""Portfolio milestone views and TPM commitment calculations."""

from __future__ import annotations

from datetime import date
from typing import Any

from program_ops.metrics import parse_date

MILESTONE_AS_OF = date(2026, 6, 2)
UPCOMING_DAYS = 30
STATUS_ORDER = {"Blocked": 0, "Missed": 1, "At Risk": 2, "On Track": 3, "Complete": 4}


def enrich_milestones(
    milestones: list[dict[str, Any]],
    programs: list[dict[str, Any]],
    as_of: date = MILESTONE_AS_OF,
) -> list[dict[str, Any]]:
    program_names = {program["id"]: program["name"] for program in programs}
    return [
        {
            **milestone,
            "program": program_names[milestone["program_id"]],
            "days_to_target": (parse_date(milestone["target_date"]) - as_of).days,
        }
        for milestone in milestones
    ]


def build_milestone_summary(
    milestones: list[dict[str, Any]],
    programs: list[dict[str, Any]],
    as_of: date = MILESTONE_AS_OF,
) -> dict[str, list[dict[str, Any]]]:
    enriched = enrich_milestones(milestones, programs, as_of)
    missed = [
        milestone
        for milestone in enriched
        if milestone["status"] == "Missed"
        or (milestone["days_to_target"] < 0 and milestone["status"] != "Complete")
    ]
    at_risk = [
        milestone for milestone in enriched if milestone["status"] in {"At Risk", "Blocked"}
    ]
    upcoming = [
        milestone
        for milestone in enriched
        if 0 <= milestone["days_to_target"] <= UPCOMING_DAYS and milestone["status"] != "Complete"
    ]
    return {
        "all": sorted(enriched, key=lambda item: (item["target_date"], item["id"])),
        "upcoming": sorted(upcoming, key=lambda item: (item["target_date"], item["id"])),
        "missed": sorted(missed, key=lambda item: (item["target_date"], item["id"])),
        "at_risk": sorted(
            at_risk,
            key=lambda item: (STATUS_ORDER.get(item["status"], 99), item["target_date"]),
        ),
    }
