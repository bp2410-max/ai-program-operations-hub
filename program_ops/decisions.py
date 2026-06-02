"""JSON-backed portfolio decision register."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DECISIONS_PATH = DATA_DIR / "decisions.json"


def load_decisions() -> list[dict[str, Any]]:
    if not DECISIONS_PATH.exists():
        return []
    return json.loads(DECISIONS_PATH.read_text(encoding="utf-8"))


def save_decision(payload: dict[str, Any]) -> dict[str, Any]:
    """Append an auditable portfolio decision to the register."""
    decision = {
        "id": f"DEC-{uuid4().hex[:8].upper()}",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        **payload,
    }
    decisions = load_decisions()
    decisions.append(decision)
    decisions.sort(key=lambda item: (item["decision_date"], item["created_at"]), reverse=True)
    DECISIONS_PATH.write_text(json.dumps(decisions, indent=2) + "\n", encoding="utf-8")
    return decision
