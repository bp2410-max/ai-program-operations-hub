"""Persist and interpret stakeholder-submitted program updates."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from program_ops.health_history import append_health_snapshot

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MANUAL_UPDATES_PATH = DATA_DIR / "manual_updates.json"

STATUS_MAP = {"Green": "On Track", "Yellow": "At Risk", "Red": "Critical"}


def analyze_manual_update(update: dict[str, Any]) -> dict[str, Any]:
    """Create a deterministic governance signal from a stakeholder submission."""
    normalized_status = STATUS_MAP[update["status"]]
    needs_attention = normalized_status != "On Track" or update["risk"] in {"High", "Critical"}
    escalation_required = update["escalation_needed"] == "Yes" or normalized_status == "Critical"
    blocker = update["blocker"].strip() or "No blocker reported"
    return {
        **update,
        "normalized_status": normalized_status,
        "needs_attention": needs_attention,
        "escalation_required": escalation_required,
        "governance_insight": (
            f"{update['stakeholder_role']} reported {update['status']} status for "
            f"{update['program_name']}. Blocker: {blocker}. ETA: {update['eta']}."
        ),
    }


def submit_manual_update(payload: dict[str, Any]) -> dict[str, Any]:
    """Append a stakeholder update to the JSON-backed MVP submission store."""
    update = analyze_manual_update(
        {
            "id": f"MUP-{uuid4().hex[:8].upper()}",
            "submitted_at": datetime.now().isoformat(timespec="seconds"),
            **payload,
        }
    )
    submissions = load_manual_updates()
    submissions.append(update)
    MANUAL_UPDATES_PATH.write_text(
        json.dumps(submissions, indent=2) + "\n",
        encoding="utf-8",
    )
    append_health_snapshot(
        {
            "program_id": update["program_id"],
            "snapshot_at": update["submitted_at"],
            "status": update["normalized_status"],
            "risk_score": update["risk_score"],
            "milestone_slip_days": update["milestone_slip_days"],
            "dependency_count": update["dependency_count"],
            "source": f"Manual update · {update['stakeholder_role']}",
            "notes": f"{update['blocker']}. ETA: {update['eta']}.",
        }
    )
    return update


def load_manual_updates() -> list[dict[str, Any]]:
    if not MANUAL_UPDATES_PATH.exists():
        return []
    return json.loads(MANUAL_UPDATES_PATH.read_text(encoding="utf-8"))
