# AI Program Operations Hub

## Product Boundary

The platform is a deterministic portfolio operations system. JSON-backed source
records, manual submissions, scoring, RAG status, risk registers, dependency
tracking, health history, governance review facts, weekly note persistence, and
the decision register must work without AI.

## Approved AI Workflows

AI may be used only for:

1. Generate Executive Summary
2. Generate Weekly Review
3. Detect Delivery Risk
4. Forecast Program Health
5. Suggest Path To Green

All future model integrations must declare an approved capability from
`program_ops.ai_policy.AI_CAPABILITIES`.

## Out Of Scope For AI

AI must not be required to:

- Store or edit authoritative portfolio records
- Calculate deterministic RAG status
- Persist stakeholder submissions
- Create health-history snapshots
- Change risk, dependency, or decision records automatically
- Send weekly emails without an explicit delivery workflow

AI outputs are advisory drafts or signals. Human-owned source data remains the
system of record.

## Integration Points

- `generate_executive_summary`: consume structured facts from
  `program_ops.governance.build_governance_review()`.
- `generate_weekly_review`: draft structured sections compatible with
  `program_ops.weekly_reviews.REVIEW_SECTIONS`.
- `detect_delivery_risk`: inspect existing records and manual submissions, then
  emit advisory risks for human review.
- `forecast_program_health`: consume snapshots from
  `data/program_health_history.json`. The deterministic baseline lives in
  `program_ops.forecasting`; a future AI forecast may augment but must not
  overwrite source records.
- `suggest_path_to_green`: propose recommendations for unhealthy programs
  without overwriting approved recovery plans.
