"""Portfolio calculations kept separate from Streamlit presentation code."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from typing import Any

STATUS_ORDER = {"Critical": 0, "At Risk": 1, "On Track": 2, "Complete": 3}
RISK_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
RAG_GUIDELINES = {
    "On Track": "No critical blockers and risk score below 30.",
    "At Risk": "Major dependency, schedule slip under 2 weeks, or risk score from 30 to 70.",
    "Critical": "Critical blocker, executive escalation, or risk score above 70.",
}


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def portfolio_summary(
    programs: list[dict[str, Any]],
    risks: list[dict[str, Any]],
    dependencies: list[dict[str, Any]],
) -> dict[str, Any]:
    assessed_programs = assess_programs(programs, risks, dependencies)
    statuses = Counter(program["status"] for program in assessed_programs)
    active_risks = [risk for risk in risks if risk["status"] not in {"Closed", "Accepted"}]
    high_risks = [risk for risk in active_risks if risk["severity"] in {"Critical", "High"}]
    blocked_dependencies = [
        dependency for dependency in dependencies if dependency["status"] in {"Blocked", "At Risk"}
    ]
    return {
        "program_count": len(assessed_programs),
        "on_track": statuses["On Track"],
        "needs_attention": statuses["At Risk"] + statuses["Critical"],
        "high_risks": len(high_risks),
        "blocked_dependencies": len(blocked_dependencies),
        "average_progress": round(
            sum(program["progress"] for program in assessed_programs) / len(assessed_programs)
        ),
    }


def assess_program_status(
    program: dict[str, Any],
    risks: list[dict[str, Any]],
    dependencies: list[dict[str, Any]],
) -> tuple[str, list[str]]:
    """Apply the portfolio RAG rules with Red taking precedence over Yellow."""
    program_risks = risks_for_program(risks, program["id"])
    program_dependencies = dependencies_for_program(dependencies, program["id"])
    score = program["risk_score"]
    slip_days = program["schedule_slip_days"]

    red_reasons = []
    if any(risk["severity"] == "Critical" for risk in program_risks) or any(
        dependency["status"] == "Blocked" for dependency in program_dependencies
    ):
        red_reasons.append("Critical blocker")
    if program["executive_escalation"]:
        red_reasons.append("Executive escalation")
    if score > 70:
        red_reasons.append(f"Risk score {score} > 70")
    if red_reasons:
        return "Critical", red_reasons

    yellow_reasons = []
    if any(dependency["status"] == "At Risk" for dependency in program_dependencies):
        yellow_reasons.append("Major dependency")
    if 0 < slip_days < 14:
        yellow_reasons.append(f"Schedule slip {slip_days} days")
    if 30 <= score <= 70:
        yellow_reasons.append(f"Risk score {score}")
    if yellow_reasons:
        return "At Risk", yellow_reasons

    return "On Track", [f"Risk score {score} < 30", "No critical blockers"]


def assess_programs(
    programs: list[dict[str, Any]],
    risks: list[dict[str, Any]],
    dependencies: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    assessed = []
    for program in programs:
        status, reasons = assess_program_status(program, risks, dependencies)
        assessed.append({**program, "status": status, "status_reasons": reasons})
    return assessed


def risks_for_program(risks: list[dict[str, Any]], program_id: str) -> list[dict[str, Any]]:
    return sorted(
        [risk for risk in risks if risk["program_id"] == program_id],
        key=lambda risk: (RISK_ORDER.get(risk["severity"], 99), risk["due_date"]),
    )


def dependencies_for_program(
    dependencies: list[dict[str, Any]], program_id: str
) -> list[dict[str, Any]]:
    return sorted(
        [dependency for dependency in dependencies if dependency["program_id"] == program_id],
        key=lambda dependency: (dependency["needed_by"], dependency["id"]),
    )


def updates_for_program(updates: list[dict[str, Any]], program_id: str) -> list[dict[str, Any]]:
    return sorted(
        [update for update in updates if update["program_id"] == program_id],
        key=lambda update: update["date"],
        reverse=True,
    )


def milestone_days_remaining(program: dict[str, Any], as_of: date | None = None) -> int:
    return (parse_date(program["next_milestone_date"]) - (as_of or date.today())).days
