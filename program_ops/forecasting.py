"""Deterministic 30-day delivery health forecasting.

This provides a transparent MVP baseline for the approved Forecast Program Health
workflow. A future AI forecast may augment the result, but source facts remain
deterministic and auditable.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from program_ops.health_history import history_for_program
from program_ops.metrics import assess_programs, parse_date

FORECAST_AS_OF = date(2026, 6, 1)
STATUS_LABELS = {"On Track": "Green", "At Risk": "Yellow", "Critical": "Red"}


def _days_since(value: str, as_of: date) -> int:
    return max(0, (as_of - parse_date(value)).days)


def build_delivery_forecasts(
    programs: list[dict[str, Any]],
    risks: list[dict[str, Any]],
    dependencies: list[dict[str, Any]],
    health_history: list[dict[str, Any]],
    as_of: date = FORECAST_AS_OF,
) -> list[dict[str, Any]]:
    assessed_programs = assess_programs(programs, risks, dependencies)
    forecasts = [
        forecast_program_health(program, risks, dependencies, health_history, as_of)
        for program in assessed_programs
    ]
    return sorted(
        forecasts,
        key=lambda item: ({"Red": 0, "Yellow": 1, "Green": 2}[item["predicted_status"]], -item["confidence"]),
    )


def forecast_program_health(
    program: dict[str, Any],
    risks: list[dict[str, Any]],
    dependencies: list[dict[str, Any]],
    health_history: list[dict[str, Any]],
    as_of: date = FORECAST_AS_OF,
) -> dict[str, Any]:
    program_risks = [
        risk
        for risk in risks
        if risk["program_id"] == program["id"] and risk["status"] not in {"Closed", "Accepted"}
    ]
    program_dependencies = [
        dependency for dependency in dependencies if dependency["program_id"] == program["id"]
    ]
    watch_dependencies = [
        dependency
        for dependency in program_dependencies
        if dependency["status"] in {"Blocked", "At Risk"}
    ]
    blocked_days = max(
        (_days_since(dependency["blocked_since"], as_of) for dependency in watch_dependencies),
        default=0,
    )
    high_risks = [
        risk for risk in program_risks if risk["severity"] in {"Critical", "High"}
    ]
    snapshots = history_for_program(health_history, program["id"])
    risk_delta = (
        snapshots[-1]["risk_score"] - snapshots[-2]["risk_score"] if len(snapshots) >= 2 else 0
    )

    if (
        program["status"] == "Critical"
        or program["risk_score"] > 70
        or any(dependency["status"] == "Blocked" for dependency in watch_dependencies)
    ):
        predicted_status = "Red"
    elif program["risk_score"] >= 30 or watch_dependencies or program["schedule_slip_days"] > 0:
        predicted_status = "Yellow"
    else:
        predicted_status = "Green"

    confidence = 70
    confidence += min(8, len(watch_dependencies) * 4)
    confidence += 4 if blocked_days > 14 else 0
    confidence += 4 if high_risks else 0
    confidence += 4 if program["status"] == {"Green": "On Track", "Yellow": "At Risk", "Red": "Critical"}[predicted_status] else 0
    confidence = min(confidence, 92)

    rationale = []
    if watch_dependencies:
        rationale.append(f"{len(watch_dependencies)} dependency commitments need attention")
    if high_risks:
        rationale.append(f"{len(high_risks)} high or critical open risks")
    if blocked_days:
        rationale.append(f"oldest blocker open {blocked_days} days")
    if risk_delta:
        direction = "up" if risk_delta > 0 else "down"
        rationale.append(f"latest recorded risk score moved {direction} {abs(risk_delta)} points")
    if not rationale:
        rationale.append("no material delivery pressure detected")

    return {
        "program_id": program["id"],
        "program_name": program["name"],
        "current_status": STATUS_LABELS[program["status"]],
        "dependency_count": len(program_dependencies),
        "open_risk_count": len(program_risks),
        "blocked_days": blocked_days,
        "predicted_status": predicted_status,
        "predicted_outcome": f"Likely {predicted_status} in 30 days",
        "confidence": confidence,
        "rationale": rationale,
    }
