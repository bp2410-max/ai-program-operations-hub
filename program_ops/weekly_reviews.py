"""JSON-backed weekly portfolio review notes."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
WEEKLY_REVIEWS_PATH = DATA_DIR / "weekly_reviews.json"
REVIEW_SECTIONS = ("highlights", "risks", "blockers", "actions", "decisions")


def load_weekly_reviews() -> list[dict[str, Any]]:
    if not WEEKLY_REVIEWS_PATH.exists():
        return []
    return json.loads(WEEKLY_REVIEWS_PATH.read_text(encoding="utf-8"))


def parse_review_items(value: str) -> list[str]:
    """Convert one-item-per-line text into a clean list."""
    return [line.strip().lstrip("-").strip() for line in value.splitlines() if line.strip()]


def save_weekly_review(payload: dict[str, Any]) -> dict[str, Any]:
    """Create or replace a weekly review while preserving its creation timestamp."""
    reviews = load_weekly_reviews()
    now = datetime.now().isoformat(timespec="seconds")
    review_id = f"WKR-{payload['week_of']}"
    existing = next((review for review in reviews if review["id"] == review_id), None)
    review = {
        "id": review_id,
        "week_of": payload["week_of"],
        "created_at": existing["created_at"] if existing else now,
        "updated_at": now,
        "author": payload["author"].strip(),
        **{section: parse_review_items(payload[section]) for section in REVIEW_SECTIONS},
    }
    reviews = [item for item in reviews if item["id"] != review_id]
    reviews.append(review)
    reviews.sort(key=lambda item: item["week_of"], reverse=True)
    WEEKLY_REVIEWS_PATH.write_text(json.dumps(reviews, indent=2) + "\n", encoding="utf-8")
    return review


def email_ready_markdown(review: dict[str, Any]) -> str:
    """Render a portable weekly brief for a future email delivery adapter."""
    lines = [f"# Week of {review['week_of']}", ""]
    for section in REVIEW_SECTIONS:
        lines.extend([f"## {section.title()}"])
        lines.extend(f"- {item}" for item in review[section])
        lines.append("")
    return "\n".join(lines).strip()
