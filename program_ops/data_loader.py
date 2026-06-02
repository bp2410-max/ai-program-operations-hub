"""JSON data access for the Program Operations Hub."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_json(filename: str) -> list[dict[str, Any]]:
    with (DATA_DIR / filename).open(encoding="utf-8") as source:
        return json.load(source)


def _load_optional_json(filename: str) -> list[dict[str, Any]]:
    path = DATA_DIR / filename
    return _load_json(filename) if path.exists() else []


def load_portfolio() -> dict[str, list[dict[str, Any]]]:
    """Load all MVP datasets from the local JSON data directory."""
    return {
        "programs": _load_json("programs.json"),
        "risks": _load_json("risks.json"),
        "dependencies": _load_json("dependencies.json"),
        "updates": _load_json("updates.json"),
        "manual_updates": _load_optional_json("manual_updates.json"),
        "health_history": _load_optional_json("program_health_history.json"),
        "weekly_reviews": _load_optional_json("weekly_reviews.json"),
        "decisions": _load_optional_json("decisions.json"),
        "milestones": _load_optional_json("milestones.json"),
    }


def program_name_map(programs: list[dict[str, Any]]) -> dict[str, str]:
    return {program["id"]: program["name"] for program in programs}


def enrich_with_program_name(
    items: list[dict[str, Any]], programs: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    names = program_name_map(programs)
    return [{**item, "program": names.get(item["program_id"], item["program_id"])} for item in items]
