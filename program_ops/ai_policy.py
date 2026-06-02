"""Allowlist for future AI-assisted workflows.

Core portfolio operations remain deterministic. Any future model integration must
declare one of these capabilities before it can be added to the product.
"""

from __future__ import annotations

from typing import Final

AI_CAPABILITIES: Final[dict[str, str]] = {
    "generate_executive_summary": "Generate Executive Summary",
    "generate_weekly_review": "Generate Weekly Review",
    "detect_delivery_risk": "Detect Delivery Risk",
    "forecast_program_health": "Forecast Program Health",
    "suggest_path_to_green": "Suggest Path To Green",
}


def require_allowed_ai_capability(capability: str) -> str:
    """Return the approved label or reject an out-of-scope AI workflow."""
    if capability not in AI_CAPABILITIES:
        raise ValueError(f"AI capability is not approved: {capability}")
    return AI_CAPABILITIES[capability]
