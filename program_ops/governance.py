"""Deterministic governance review facts and summary generation.

The structured review returned here is intentionally presentation-neutral. Future
AI support may generate an executive summary from these facts without changing the
deterministic governance calculations or Streamlit views.
"""

from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any

from program_ops.metrics import RISK_ORDER, STATUS_ORDER, assess_programs, parse_date

GOVERNANCE_AS_OF = date(2026, 6, 1)
NEW_RISK_DAYS = 14
AGING_RISK_DAYS = 30
AGING_BLOCKER_DAYS = 14


def _days_since(value: str, as_of: date) -> int:
    return (as_of - parse_date(value)).days


def build_governance_review(
    programs: list[dict[str, Any]],
    risks: list[dict[str, Any]],
    dependencies: list[dict[str, Any]],
    manual_updates: list[dict[str, Any]] | None = None,
    as_of: date = GOVERNANCE_AS_OF,
) -> dict[str, Any]:
    assessed_programs = assess_programs(programs, risks, dependencies)
    program_names = {program["id"]: program["name"] for program in assessed_programs}
    active_risks = [
        {**risk, "age_days": _days_since(risk["identified_date"], as_of)}
        for risk in risks
        if risk["status"] not in {"Closed", "Accepted"}
    ]
    tracked_dependencies = [
        {
            **dependency,
            "program": program_names[dependency["program_id"]],
            "age_days": _days_since(dependency["blocked_since"], as_of),
        }
        for dependency in dependencies
    ]
    status_counts = Counter(program["status"] for program in assessed_programs)
    unhealthy_programs = [
        program for program in assessed_programs if program["status"] in {"Critical", "At Risk"}
    ]
    unhealthy_programs.sort(
        key=lambda program: (STATUS_ORDER.get(program["status"], 99), -program["risk_score"])
    )
    watch_dependencies = [
        dependency
        for dependency in tracked_dependencies
        if dependency["status"] in {"Blocked", "At Risk"}
    ]
    watch_dependencies.sort(
        key=lambda dependency: (
            {"Blocked": 0, "At Risk": 1}.get(dependency["status"], 99),
            -dependency["age_days"],
        )
    )
    aging_risks = [risk for risk in active_risks if risk["age_days"] > AGING_RISK_DAYS]
    aging_risks.sort(key=lambda risk: (-risk["age_days"], RISK_ORDER.get(risk["severity"], 99)))
    new_risks = [risk for risk in active_risks if risk["age_days"] <= NEW_RISK_DAYS]
    new_risks.sort(key=lambda risk: (RISK_ORDER.get(risk["severity"], 99), -risk["age_days"]))
    aging_blockers = [
        dependency
        for dependency in watch_dependencies
        if dependency["age_days"] > AGING_BLOCKER_DAYS
    ]
    escalation_programs = [
        program
        for program in unhealthy_programs
        if program["recovery"]["escalation_needed"] == "Yes"
    ]
    top_risks = sorted(
        active_risks,
        key=lambda risk: (RISK_ORDER.get(risk["severity"], 99), -risk["age_days"]),
    )[:5]
    portfolio_health = min(
        (program["status"] for program in assessed_programs),
        key=lambda status: STATUS_ORDER.get(status, 99),
    )
    stakeholder_signals = sorted(
        manual_updates or [],
        key=lambda update: update["submitted_at"],
        reverse=True,
    )
    review = {
        "as_of": as_of,
        "portfolio_health": portfolio_health,
        "status_counts": status_counts,
        "new_risks": new_risks,
        "top_risks": top_risks,
        "aging_risks": aging_risks,
        "blocked_programs": unhealthy_programs,
        "escalation_programs": escalation_programs,
        "aging_blockers": aging_blockers,
        "top_programs": unhealthy_programs[:5],
        "top_dependencies": watch_dependencies[:5],
        "path_to_green": [
            {"program": program["name"], "recommendation": program["recovery"]["path_to_green"]}
            for program in unhealthy_programs
        ],
        "stakeholder_signals": stakeholder_signals,
        "manual_escalations": [
            update for update in stakeholder_signals if update["escalation_required"]
        ],
    }
    review["executive_summary"] = build_executive_summary(review)
    return review


def build_executive_summary(review: dict[str, Any]) -> list[str]:
    """Build today's deterministic fallback for the approved executive-summary workflow."""
    counts = review["status_counts"]
    summary = [
        (
            f"Portfolio health is {review['portfolio_health']}: {counts['Critical']} Red, "
            f"{counts['At Risk']} Yellow, and {counts['On Track']} Green programs."
        ),
        (
            f"{len(review['aging_risks'])} risks have been open longer than {AGING_RISK_DAYS} days "
            "and require leadership awareness."
        ),
        (
            f"{len(review['escalation_programs'])} program requires executive action; "
            "Cloud Migration remains the primary portfolio concern."
        ),
    ]
    if review["stakeholder_signals"]:
        summary.append(
            f"{len(review['stakeholder_signals'])} manual stakeholder updates are available; "
            f"{len(review['manual_escalations'])} require escalation review."
        )
    return summary
