"""JSON-backed historical program health snapshots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
HEALTH_HISTORY_PATH = DATA_DIR / "program_health_history.json"
HEALTH_SCORE = {"Critical": 1, "At Risk": 2, "On Track": 3}


def load_health_history() -> list[dict[str, Any]]:
    if not HEALTH_HISTORY_PATH.exists():
        return []
    return json.loads(HEALTH_HISTORY_PATH.read_text(encoding="utf-8"))


def history_for_program(
    history: list[dict[str, Any]], program_id: str
) -> list[dict[str, Any]]:
    snapshots = [snapshot for snapshot in history if snapshot["program_id"] == program_id]
    return sorted(snapshots, key=lambda snapshot: snapshot["snapshot_at"])


def append_health_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    stored_snapshot = {
        "id": f"HST-{uuid4().hex[:8].upper()}",
        **snapshot,
    }
    history = load_health_history()
    history.append(stored_snapshot)
    HEALTH_HISTORY_PATH.write_text(json.dumps(history, indent=2) + "\n", encoding="utf-8")
    return stored_snapshot
