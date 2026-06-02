"""Streamlit views for the TPM portfolio MVP."""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
import streamlit as st

from program_ops.data_loader import enrich_with_program_name
from program_ops.decisions import save_decision
from program_ops.governance import build_governance_review
from program_ops.forecasting import FORECAST_AS_OF, build_delivery_forecasts, forecast_program_health
from program_ops.health_history import HEALTH_SCORE, history_for_program
from program_ops.metrics import (
    RAG_GUIDELINES,
    STATUS_ORDER,
    assess_programs,
    dependencies_for_program,
    milestone_days_remaining,
    portfolio_summary,
    risks_for_program,
    updates_for_program,
)
from program_ops.milestones import MILESTONE_AS_OF, build_milestone_summary
from program_ops.submissions import submit_manual_update
from program_ops.weekly_reviews import REVIEW_SECTIONS, email_ready_markdown, save_weekly_review

STATUS_COLORS = {
    "On Track": "#16794b",
    "At Risk": "#b46a00",
    "Critical": "#b42318",
    "Blocked": "#b42318",
    "Mitigating": "#175cd3",
    "Monitoring": "#475467",
    "Escalated": "#b42318",
    "High": "#b46a00",
    "Medium": "#175cd3",
    "Low": "#475467",
    "Green": "#16794b",
    "Yellow": "#b46a00",
    "Red": "#b42318",
    "Pending": "#b46a00",
    "Approved": "#16794b",
    "Revisit": "#175cd3",
    "Missed": "#b42318",
}


def _status_badge(status: str) -> str:
    color = STATUS_COLORS.get(status, "#475467")
    return (
        f"<span style='background:{color}18;color:{color};border:1px solid {color}55;"
        f"border-radius:999px;padding:0.2rem 0.55rem;font-size:0.78rem;font-weight:700'>"
        f"{status}</span>"
    )


def _format_date(value: str) -> str:
    return pd.to_datetime(value).strftime("%b %d, %Y")


def _render_rag_guidelines() -> None:
    with st.expander("RAG status guidelines"):
        st.markdown(
            f"""
            **Green · On Track**  
            {RAG_GUIDELINES["On Track"]}

            **Yellow · At Risk**  
            {RAG_GUIDELINES["At Risk"]}

            **Red · Critical**  
            {RAG_GUIDELINES["Critical"]}
            """
        )


def _render_recovery_summary(program: dict[str, Any]) -> None:
    recovery = program["recovery"]
    st.markdown(f"#### {program['name']}")
    st.markdown(_status_badge(program["status"]), unsafe_allow_html=True)
    st.write(f"**Primary driver:** {recovery['primary_driver']}")
    st.write(f"**Blocking dependency:** {recovery['blocking_dependency']}")
    columns = st.columns(3)
    columns[0].write(f"**Risk owner:** {recovery['risk_owner']}")
    columns[1].write(f"**ETA to unblock:** {_format_date(recovery['eta_to_unblock'])}")
    columns[2].write(f"**Escalation needed:** {recovery['escalation_needed']}")
    st.write(f"**Next action:** {recovery['next_action']}")
    st.write(f"**Path to green:** {recovery['path_to_green']}")


def _render_stakeholder_callouts(program: dict[str, Any]) -> None:
    for stakeholder, callout in program["stakeholder_callouts"].items():
        with st.expander(stakeholder):
            st.write(f"**What to care about:** {callout['care_about']}")
            st.write(f"**Action needed:** {callout['action']}")
            st.write(f"**Deadline or ETA:** {_format_date(callout['deadline'])}")
            st.write(f"**Path to green:** {callout['path_to_green']}")


def _render_manual_signal(update: dict[str, Any]) -> None:
    st.markdown(f"**{update['program_name']} · {update['stakeholder_role']}**")
    st.markdown(_status_badge(update["status"]), unsafe_allow_html=True)
    st.write(update["governance_insight"])
    st.caption(
        f"Submitted by {update['submitted_by']} · Risk: {update['risk']} · "
        f"Escalation: {update['escalation_needed']}"
    )


def _render_health_history(history: list[dict[str, Any]], program_id: str) -> None:
    snapshots = history_for_program(history, program_id)
    if not snapshots:
        st.info("No health snapshots recorded yet.")
        return

    frame = pd.DataFrame(snapshots)
    frame["snapshot"] = pd.to_datetime(frame["snapshot_at"])
    frame["health_score"] = frame["status"].map(HEALTH_SCORE)
    frame["status_change"] = frame["status"].where(frame["status"].ne(frame["status"].shift()))
    frame["risk_score_change"] = frame["risk_score"].diff()
    frame["milestone_slip_change"] = frame["milestone_slip_days"].diff()
    frame["dependency_count_change"] = frame["dependency_count"].diff()

    st.subheader("Program Health History")
    st.caption("Historical snapshots from governance reviews and stakeholder submissions")
    trend_left, trend_right = st.columns(2)
    with trend_left:
        st.markdown("**Health trend**")
        st.line_chart(
            frame.set_index("snapshot")[["health_score", "milestone_slip_days", "dependency_count"]],
            height=260,
        )
        st.caption("Health score: Critical = 1 · At Risk = 2 · On Track = 3")
    with trend_right:
        st.markdown("**Risk trend**")
        st.line_chart(frame.set_index("snapshot")[["risk_score"]], height=260)

    st.markdown("**Status timeline**")
    timeline = frame.rename(
        columns={
            "snapshot": "Snapshot",
            "status": "Status",
            "status_change": "Status change",
            "risk_score": "Risk score",
            "risk_score_change": "Risk score change",
            "milestone_slip_days": "Milestone slip days",
            "milestone_slip_change": "Slip change",
            "dependency_count": "Dependencies",
            "dependency_count_change": "Dependency change",
            "source": "Source",
            "notes": "Notes",
        }
    )
    st.dataframe(
        timeline[
            [
                "Snapshot",
                "Status",
                "Status change",
                "Risk score",
                "Risk score change",
                "Milestone slip days",
                "Slip change",
                "Dependencies",
                "Dependency change",
                "Source",
                "Notes",
            ]
        ],
        hide_index=True,
        width="stretch",
    )


def _render_delivery_forecast(forecast: dict[str, Any]) -> None:
    st.markdown(f"#### {forecast['program_name']}")
    st.markdown(_status_badge(forecast["predicted_status"]), unsafe_allow_html=True)
    forecast_cols = st.columns(4)
    forecast_cols[0].metric("Current", forecast["current_status"])
    forecast_cols[1].metric("Dependencies", forecast["dependency_count"])
    forecast_cols[2].metric("Open risks", forecast["open_risk_count"])
    forecast_cols[3].metric("Blocked", f"{forecast['blocked_days']} days")
    st.write(f"**Predicted outcome:** {forecast['predicted_outcome']}")
    st.write(f"**Confidence:** {forecast['confidence']}%")
    st.caption(f"Drivers: {' · '.join(forecast['rationale'])}")


def render_dashboard(data: dict[str, list[dict[str, Any]]]) -> None:
    risks, dependencies = data["risks"], data["dependencies"]
    programs = assess_programs(data["programs"], risks, dependencies)
    summary = portfolio_summary(programs, risks, dependencies)
    st.title("Portfolio Dashboard")
    st.caption("Acme Cloud executive view of active product, platform, infrastructure, and security programs")
    _render_rag_guidelines()

    st.subheader("Overall system health")
    overall_status = min(
        (program["status"] for program in programs),
        key=lambda status: STATUS_ORDER.get(status, 99),
    )
    health_cols = st.columns(4)
    health_cols[0].metric("Portfolio health", overall_status)
    health_cols[1].metric("Green · On track", summary["on_track"])
    health_cols[2].metric(
        "Yellow · At risk", sum(program["status"] == "At Risk" for program in programs)
    )
    health_cols[3].metric(
        "Red · Critical", sum(program["status"] == "Critical" for program in programs)
    )

    cols = st.columns(4)
    cards = [
        ("Active programs", summary["program_count"]),
        ("High risks", summary["high_risks"]),
        ("Dependency watch", summary["blocked_dependencies"]),
        ("Average progress", f"{summary['average_progress']}%"),
    ]
    for column, (label, value) in zip(cols, cards):
        column.metric(label, value)

    st.subheader("Program health")
    for program in sorted(programs, key=lambda item: STATUS_ORDER.get(item["status"], 99)):
        with st.container(border=True):
            heading, progress, milestone = st.columns([2.5, 1.2, 1.4])
            heading.markdown(f"#### {program['name']}")
            heading.markdown(_status_badge(program["status"]), unsafe_allow_html=True)
            heading.caption(f"{program['team']} · {program['portfolio']} · Owner: {program['owner']}")
            heading.caption(f"Assessment: {' · '.join(program['status_reasons'])}")
            progress.metric("Progress", f"{program['progress']}%")
            progress.progress(program["progress"] / 100)
            milestone.caption("Next milestone")
            milestone.write(program["next_milestone"])
            milestone.caption(_format_date(program["next_milestone_date"]))

    st.subheader("Executive attention")
    attention = [program for program in programs if program["status"] in {"Critical", "At Risk"}]
    for program in attention:
        st.warning(f"**{program['name']}**: {program['executive_attention']}")

    st.subheader("Red and Yellow recovery snapshot")
    st.caption("What is driving unhealthy programs and what needs to happen next")
    for program in attention:
        with st.container(border=True):
            _render_recovery_summary(program)

    if data["manual_updates"]:
        st.subheader("Latest stakeholder signals")
        st.caption("Manual updates submitted by delivery and operating teams")
        for update in sorted(
            data["manual_updates"], key=lambda item: item["submitted_at"], reverse=True
        )[:5]:
            with st.container(border=True):
                _render_manual_signal(update)


def render_program_details(data: dict[str, list[dict[str, Any]]]) -> None:
    programs = assess_programs(data["programs"], data["risks"], data["dependencies"])
    st.title("Program Details")
    st.caption("Milestones, decisions, delivery health, and latest operating updates")
    selected_name = st.selectbox("Select program", [program["name"] for program in programs])
    program = next(program for program in programs if program["name"] == selected_name)
    program_risks = risks_for_program(data["risks"], program["id"])
    program_dependencies = dependencies_for_program(data["dependencies"], program["id"])
    program_updates = updates_for_program(data["updates"], program["id"])
    manual_updates = [
        update for update in data["manual_updates"] if update["program_id"] == program["id"]
    ]
    milestone_summary = build_milestone_summary(data["milestones"], data["programs"])
    program_milestones = [
        milestone
        for milestone in milestone_summary["all"]
        if milestone["program_id"] == program["id"]
    ]
    forecast = forecast_program_health(
        program,
        data["risks"],
        data["dependencies"],
        data["health_history"],
    )

    st.markdown(f"## {program['name']}")
    st.markdown(_status_badge(program["status"]), unsafe_allow_html=True)
    st.write(program["summary"])

    cols = st.columns(5)
    cols[0].metric("Progress", f"{program['progress']}%")
    cols[1].metric("Phase", program["phase"])
    cols[2].metric("Budget", f"${program['budget_m']:.1f}M")
    cols[3].metric("Risk score", program["risk_score"])
    cols[4].metric("Target date", _format_date(program["target_date"]))
    st.progress(program["progress"] / 100)
    st.caption(
        f"RAG assessment: {' · '.join(program['status_reasons'])} · "
        f"Schedule slip: {program['schedule_slip_days']} days"
    )

    st.subheader("Why this status?")
    st.markdown(f"**Current status:** {forecast['current_status']}")
    if program["status"] == "On Track":
        st.success("This program is Green because it has no critical blockers and remains below the risk score threshold.")
    elif program["status"] == "At Risk":
        st.warning("This program is Yellow because it has recoverable delivery pressure that needs active mitigation.")
    else:
        st.error("This program is Red because it has a critical blocker or executive-level escalation.")
    st.markdown("**Drivers:**")
    for reason in forecast["rationale"]:
        st.write(f"- {reason}")
    if program["status"] in {"Critical", "At Risk"}:
        st.write(f"**Path to green:** {program['recovery']['path_to_green']}")
    else:
        st.write("**Path to green:** Maintain current risk score below 30 and close planned dependencies on schedule.")

    st.subheader("30-day delivery forecast")
    with st.container(border=True):
        _render_delivery_forecast(forecast)

    _render_health_history(data["health_history"], program["id"])

    if program["status"] in {"Critical", "At Risk"}:
        st.subheader("Recovery plan")
        with st.container(border=True):
            _render_recovery_summary(program)

    st.subheader("Stakeholder interpretation")
    st.caption("Role-specific focus, next action, deadline, and path to green")
    _render_stakeholder_callouts(program)

    left, right = st.columns(2)
    with left:
        st.subheader("Next milestone")
        st.write(f"**{program['next_milestone']}**")
        st.caption(
            f"{_format_date(program['next_milestone_date'])} · "
            f"{milestone_days_remaining(program, date(2026, 6, 1))} days remaining"
        )
    with right:
        st.subheader("Executive attention")
        if program["status"] in {"Critical", "At Risk"}:
            st.warning(program["executive_attention"])
        else:
            st.success(program["executive_attention"])

    st.subheader("Program register")
    register_cols = st.columns(3)
    register_cols[0].metric("Active risks", len(program_risks))
    register_cols[1].metric(
        "Risk dependencies",
        sum(dep["status"] in {"Blocked", "At Risk"} for dep in program_dependencies),
    )
    register_cols[2].metric("Latest update", _format_date(program_updates[0]["date"]))

    st.subheader("Milestone commitments")
    for milestone in program_milestones:
        with st.container(border=True):
            _render_milestone(milestone)

    st.subheader("Risks and dependencies")
    details_left, details_right = st.columns(2)
    with details_left:
        for risk in program_risks:
            st.markdown(f"**{risk['title']}**")
            st.caption(f"{risk['severity']} · {risk['risk_type']} risk · Owner: {risk['owner']}")
    with details_right:
        for dependency in program_dependencies:
            st.markdown(f"**{dependency['blocked_team']} ← {dependency['owner']}**")
            st.caption(f"{dependency['status']} · ETA: {_format_date(dependency['unblock_eta'])}")

    st.subheader("Recent updates")
    for update in program_updates:
        with st.container(border=True):
            st.markdown(f"**{_format_date(update['date'])} · {update['author']}**")
            st.write(update["summary"])

    if manual_updates:
        st.subheader("Stakeholder-submitted updates")
        for update in sorted(manual_updates, key=lambda item: item["submitted_at"], reverse=True):
            with st.container(border=True):
                _render_manual_signal(update)


def render_risks(data: dict[str, list[dict[str, Any]]]) -> None:
    st.title("Risk Register")
    st.caption("Existing and potential risks with leadership, program, engineering, and customer-facing callouts")
    programs = assess_programs(data["programs"], data["risks"], data["dependencies"])
    risks = enrich_with_program_name(data["risks"], data["programs"])
    severity_filter = st.multiselect(
        "Severity", ["Critical", "High", "Medium", "Low"], default=["Critical", "High", "Medium", "Low"]
    )
    visible = [risk for risk in risks if risk["severity"] in severity_filter]
    visible.sort(key=lambda risk: ({"Critical": 0, "High": 1, "Medium": 2, "Low": 3}[risk["severity"]], risk["due_date"]))

    st.subheader("Red and Yellow recovery summary")
    for program in programs:
        if program["status"] in {"Critical", "At Risk"}:
            with st.container(border=True):
                _render_recovery_summary(program)

    st.subheader("Stakeholder interpretation")
    st.caption("Choose a program to review stakeholder-specific callouts without leaving the risk register")
    selected_name = st.selectbox(
        "Program interpretation",
        [program["name"] for program in programs],
        key="risk_program_interpretation",
    )
    selected_program = next(program for program in programs if program["name"] == selected_name)
    _render_stakeholder_callouts(selected_program)

    if data["manual_updates"]:
        st.subheader("Latest stakeholder risk signals")
        for update in sorted(
            data["manual_updates"], key=lambda item: item["submitted_at"], reverse=True
        )[:5]:
            with st.container(border=True):
                _render_manual_signal(update)

    st.subheader("Risk inventory")
    for risk in visible:
        with st.container(border=True):
            title, owner, due = st.columns([2.4, 1.1, 1])
            title.markdown(f"#### {risk['title']}")
            title.markdown(_status_badge(risk["severity"]), unsafe_allow_html=True)
            title.caption(f"{risk['id']} · {risk['program']} · {risk['risk_type']} · {risk['category']}")
            owner.caption("Owner")
            owner.write(risk["owner"])
            due.caption("Mitigation due")
            due.write(_format_date(risk["due_date"]))
            st.write(f"**Mitigation:** {risk['mitigation']}")
            st.caption(
                f"State: {risk['status']} · Probability: {risk['probability']} · "
                f"Team callouts: {', '.join(risk['team_callouts'])}"
            )


def render_dependencies(data: dict[str, list[dict[str, Any]]]) -> None:
    st.title("Dependency Tracker")
    st.caption("Who is blocking whom, whether the factor is internal or external, and the path to green")
    dependencies = enrich_with_program_name(data["dependencies"], data["programs"])
    status_filter = st.multiselect(
        "Status", ["Blocked", "At Risk", "On Track"], default=["Blocked", "At Risk", "On Track"]
    )
    visible = [dependency for dependency in dependencies if dependency["status"] in status_filter]
    visible.sort(key=lambda dependency: ({"Blocked": 0, "At Risk": 1, "On Track": 2}[dependency["status"]], dependency["needed_by"]))

    if not visible:
        st.info("No dependencies match the selected filters.")
        return

    for dependency in visible:
        with st.container(border=True):
            heading, eta = st.columns([3, 1])
            heading.markdown(
                f"#### {dependency['blocked_team']} ← {dependency['owner']}"
            )
            heading.markdown(_status_badge(dependency["status"]), unsafe_allow_html=True)
            heading.caption(
                f"{dependency['program']} · {dependency['factor']} factor · "
                f"{dependency['type']} · {dependency['id']}"
            )
            eta.caption("ETA to unblock")
            eta.write(_format_date(dependency["unblock_eta"]))
            st.write(f"**Dependency:** {dependency['dependency']}")
            st.write(f"**Impact:** {dependency['impact']}")
            st.write(f"**Path to green:** {dependency['path_to_green']}")


def render_governance_review(data: dict[str, list[dict[str, Any]]]) -> None:
    review = build_governance_review(
        data["programs"], data["risks"], data["dependencies"], data["manual_updates"]
    )
    st.title("Governance Review")
    st.caption(
        f"Leadership portfolio review · Snapshot as of {_format_date(review['as_of'].isoformat())}"
    )

    st.subheader("Executive summary")
    with st.container(border=True):
        for summary_line in review["executive_summary"]:
            st.write(f"- {summary_line}")

    st.subheader("Portfolio health")
    counts = review["status_counts"]
    health_cols = st.columns(4)
    health_cols[0].metric("Portfolio health", review["portfolio_health"])
    health_cols[1].metric("Green · On track", counts["On Track"])
    health_cols[2].metric("Yellow · At risk", counts["At Risk"])
    health_cols[3].metric("Red · Critical", counts["Critical"])

    st.subheader("Top risks")
    st.caption("Executive view only. Use the Risks page for detailed management.")
    for risk in review["top_risks"]:
        with st.container(border=True):
            st.markdown(f"#### {risk['title']}")
            st.markdown(_status_badge(risk["severity"]), unsafe_allow_html=True)
            st.caption(f"{risk['category']} · {risk['age_days']} days open · Owner: {risk['owner']}")
            st.write(f"**Mitigation:** {risk['mitigation']}")

    st.subheader("Aging risks")
    for risk in review["aging_risks"]:
        st.warning(
            f"**{risk['title']}** · {risk['age_days']} days open · "
            f"{risk['severity']} · Owner: {risk['owner']}"
        )

    st.subheader("Escalations")
    for program in review["escalation_programs"]:
        with st.container(border=True):
            st.markdown(f"#### {program['name']}")
            st.markdown(_status_badge(program["status"]), unsafe_allow_html=True)
            st.write(f"**Executive action:** {program['executive_attention']}")
            st.write(f"**Path to green:** {program['recovery']['path_to_green']}")


def render_delivery_forecasting(data: dict[str, list[dict[str, Any]]]) -> None:
    st.title("Delivery Forecasting")
    st.caption(
        f"Deterministic 30-day delivery outlook · Snapshot as of {_format_date(FORECAST_AS_OF.isoformat())}"
    )
    st.info("Forecasts are rule-based and auditable. No AI model is used yet.")
    forecasts = build_delivery_forecasts(
        data["programs"],
        data["risks"],
        data["dependencies"],
        data["health_history"],
    )
    for forecast in forecasts:
        with st.container(border=True):
            _render_delivery_forecast(forecast)


def _render_milestone(milestone: dict[str, Any]) -> None:
    heading, target = st.columns([3, 1])
    heading.markdown(f"#### {milestone['milestone']}")
    heading.markdown(_status_badge(milestone["status"]), unsafe_allow_html=True)
    heading.caption(f"{milestone['program']} · {milestone['id']} · Owner: {milestone['owner']}")
    target.caption("Target date")
    target.write(_format_date(milestone["target_date"]))
    st.write(f"**Deliverable:** {milestone['deliverable']}")
    st.write(f"**Commitment:** {milestone['commitment']}")
    if milestone["notes"]:
        st.caption(milestone["notes"])


def render_milestones(data: dict[str, list[dict[str, Any]]]) -> None:
    summary = build_milestone_summary(data["milestones"], data["programs"])
    st.title("Milestones")
    st.caption(
        f"TPM commitments, deliverables, and target dates · Snapshot as of "
        f"{_format_date(MILESTONE_AS_OF.isoformat())}"
    )

    metric_cols = st.columns(4)
    metric_cols[0].metric("Total milestones", len(summary["all"]))
    metric_cols[1].metric("Upcoming · 30 days", len(summary["upcoming"]))
    metric_cols[2].metric("At risk or blocked", len(summary["at_risk"]))
    metric_cols[3].metric("Missed", len(summary["missed"]))

    st.subheader("Missed milestones")
    for milestone in summary["missed"]:
        with st.container(border=True):
            _render_milestone(milestone)

    st.subheader("Milestones at risk")
    for milestone in summary["at_risk"]:
        with st.container(border=True):
            _render_milestone(milestone)

    st.subheader("Upcoming milestones")
    for milestone in summary["upcoming"]:
        with st.container(border=True):
            _render_milestone(milestone)


def render_manual_update(data: dict[str, list[dict[str, Any]]]) -> None:
    st.title("Submit Update")
    st.caption("Capture a stakeholder update and surface it as a governance signal")

    with st.form("manual_update_form", clear_on_submit=True):
        identity_cols = st.columns(2)
        submitted_by = identity_cols[0].text_input("Your name")
        stakeholder_role = identity_cols[1].selectbox(
            "Your role",
            [
                "TPM / Program Manager",
                "Engineering Manager",
                "Customer Support Manager",
                "Product Manager",
                "Leadership / Executive team",
                "Other stakeholder",
            ],
        )
        program_name = st.selectbox(
            "Program",
            [program["name"] for program in data["programs"]],
        )
        program = next(program for program in data["programs"] if program["name"] == program_name)
        signal_cols = st.columns(3)
        status = signal_cols[0].selectbox("Status", ["Green", "Yellow", "Red"])
        risk = signal_cols[1].selectbox("Risk", ["Low", "Medium", "High", "Critical"])
        escalation_needed = signal_cols[2].selectbox("Escalation needed", ["No", "Yes"])
        dependency_default = sum(
            dependency["program_id"] == program["id"] for dependency in data["dependencies"]
        )
        history_cols = st.columns(3)
        risk_score = history_cols[0].number_input(
            "Risk score", min_value=0, max_value=100, value=program["risk_score"]
        )
        milestone_slip_days = history_cols[1].number_input(
            "Milestone slip days", min_value=0, value=program["schedule_slip_days"]
        )
        dependency_count = history_cols[2].number_input(
            "Dependency count", min_value=0, value=dependency_default
        )
        blocker = st.text_area("Blocker or concern", placeholder="Example: API stabilization delayed")
        eta = st.text_input("ETA to unblock", placeholder="Example: 2 weeks or Jun 18, 2026")
        next_action = st.text_area("Next action needed")
        path_to_green = st.text_area("Path to green")
        notes = st.text_area("Additional context", placeholder="Optional stakeholder notes")
        submitted = st.form_submit_button("Submit governance update", type="primary")

    if submitted:
        required = {
            "Your name": submitted_by,
            "Blocker or concern": blocker,
            "ETA to unblock": eta,
            "Next action needed": next_action,
            "Path to green": path_to_green,
        }
        missing = [label for label, value in required.items() if not value.strip()]
        if missing:
            st.error(f"Complete the required fields: {', '.join(missing)}.")
        else:
            update = submit_manual_update(
                {
                    "program_id": program["id"],
                    "program_name": program_name,
                    "submitted_by": submitted_by.strip(),
                    "stakeholder_role": stakeholder_role,
                    "status": status,
                    "blocker": blocker.strip(),
                    "eta": eta.strip(),
                    "risk": risk,
                    "risk_score": risk_score,
                    "milestone_slip_days": milestone_slip_days,
                    "dependency_count": dependency_count,
                    "next_action": next_action.strip(),
                    "path_to_green": path_to_green.strip(),
                    "escalation_needed": escalation_needed,
                    "notes": notes.strip(),
                }
            )
            st.success(f"Update {update['id']} submitted and added to governance insights.")

    if data["manual_updates"]:
        st.subheader("Recent submissions")
        for update in sorted(
            data["manual_updates"], key=lambda item: item["submitted_at"], reverse=True
        )[:5]:
            with st.container(border=True):
                _render_manual_signal(update)


def _render_weekly_review(review: dict[str, Any]) -> None:
    st.markdown(f"## Week of {_format_date(review['week_of'])}")
    st.caption(f"Owner: {review['author']} · Updated: {_format_date(review['updated_at'][:10])}")
    for section in REVIEW_SECTIONS:
        st.markdown(f"### {section.title()}")
        if review[section]:
            for item in review[section]:
                st.write(f"- {item}")
        else:
            st.caption("No items recorded.")


def render_weekly_review(data: dict[str, list[dict[str, Any]]]) -> None:
    st.title("Weekly Review Notes")
    st.caption("Create an email-ready portfolio brief for the weekly operating cadence")
    reviews = sorted(data["weekly_reviews"], key=lambda review: review["week_of"], reverse=True)

    with st.expander("Create or update weekly review"):
        with st.form("weekly_review_form"):
            week_of = st.date_input("Week of")
            author = st.text_input("Review owner", value="Portfolio Operations")
            st.caption("Enter one concise item per line.")
            fields = {
                section: st.text_area(section.title(), height=120)
                for section in REVIEW_SECTIONS
            }
            submitted = st.form_submit_button("Save weekly review", type="primary")

        if submitted:
            if not author.strip():
                st.error("Review owner is required.")
            elif not any(value.strip() for value in fields.values()):
                st.error("Add at least one weekly review note.")
            else:
                review = save_weekly_review(
                    {
                        "week_of": week_of.isoformat(),
                        "author": author,
                        **fields,
                    }
                )
                st.success(f"Weekly review for {_format_date(review['week_of'])} saved.")

    if not reviews:
        st.info("No weekly review notes have been saved yet.")
        return

    selected_week = st.selectbox(
        "Review week",
        [review["week_of"] for review in reviews],
        format_func=_format_date,
    )
    selected_review = next(review for review in reviews if review["week_of"] == selected_week)
    with st.container(border=True):
        _render_weekly_review(selected_review)

    st.subheader("Email-ready preview")
    st.caption("Structured for a future email delivery integration; no email is sent yet.")
    with st.container(border=True):
        st.markdown(f"**Subject:** Acme Cloud Program Operations Review · Week of {_format_date(selected_week)}")
        st.markdown(email_ready_markdown(selected_review))


def render_decision_register(data: dict[str, list[dict[str, Any]]]) -> None:
    st.title("Decision Register")
    st.caption("Record portfolio decisions, rationale, owners, and follow-up actions")

    with st.expander("Record decision"):
        with st.form("decision_register_form", clear_on_submit=True):
            decision_date = st.date_input("Decision date")
            program_name = st.selectbox(
                "Program",
                [program["name"] for program in data["programs"]],
            )
            program = next(program for program in data["programs"] if program["name"] == program_name)
            decision = st.text_area("Decision", placeholder="Example: Delay rollout by 2 weeks")
            reason = st.text_area("Reason", placeholder="Example: API instability")
            form_cols = st.columns(2)
            owner = form_cols[0].text_input("Owner", placeholder="Example: Platform Team")
            status = form_cols[1].selectbox("Status", ["Pending", "Approved", "Revisit"])
            follow_up = st.text_area("Follow-up action", placeholder="Optional next step or review date")
            submitted = st.form_submit_button("Save decision", type="primary")

        if submitted:
            required = {"Decision": decision, "Reason": reason, "Owner": owner}
            missing = [label for label, value in required.items() if not value.strip()]
            if missing:
                st.error(f"Complete the required fields: {', '.join(missing)}.")
            else:
                saved = save_decision(
                    {
                        "decision_date": decision_date.isoformat(),
                        "program_id": program["id"],
                        "program_name": program_name,
                        "decision": decision.strip(),
                        "reason": reason.strip(),
                        "owner": owner.strip(),
                        "status": status,
                        "follow_up": follow_up.strip(),
                    }
                )
                st.success(f"Decision {saved['id']} added to the register.")

    decisions = sorted(
        data["decisions"],
        key=lambda item: (item["decision_date"], item["created_at"]),
        reverse=True,
    )
    if not decisions:
        st.info("No portfolio decisions have been recorded yet.")
        return

    filters = st.columns(2)
    program_filter = filters[0].selectbox(
        "Filter by program",
        ["All programs", *[program["name"] for program in data["programs"]]],
    )
    status_filter = filters[1].multiselect(
        "Filter by status",
        ["Pending", "Approved", "Revisit"],
        default=["Pending", "Approved", "Revisit"],
    )
    visible = [
        decision
        for decision in decisions
        if (program_filter == "All programs" or decision["program_name"] == program_filter)
        and decision["status"] in status_filter
    ]

    st.subheader("Decision timeline")
    for decision in visible:
        with st.container(border=True):
            heading, decision_status = st.columns([3, 1])
            heading.markdown(f"#### {_format_date(decision['decision_date'])} · {decision['program_name']}")
            heading.caption(f"{decision['id']} · Owner: {decision['owner']}")
            decision_status.markdown(_status_badge(decision["status"]), unsafe_allow_html=True)
            st.write(f"**Decision:** {decision['decision']}")
            st.write(f"**Reason:** {decision['reason']}")
            if decision["follow_up"]:
                st.write(f"**Follow-up:** {decision['follow_up']}")
