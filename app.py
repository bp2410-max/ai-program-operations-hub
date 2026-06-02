"""AI Program Operations Hub MVP.

The initial release intentionally uses synthetic JSON data and does not include AI features.
"""

import streamlit as st

from program_ops.data_loader import load_portfolio
from program_ops.views import (
    render_dashboard,
    render_decision_register,
    render_delivery_forecasting,
    render_dependencies,
    render_governance_review,
    render_manual_update,
    render_milestones,
    render_program_details,
    render_risks,
    render_weekly_review,
)

st.set_page_config(
    page_title="AI Program Operations Hub",
    page_icon=":material/dashboard:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1440px;}
    [data-testid="stSidebar"] {background: #f7f9fc;}
    [data-testid="stMetric"] {
        background: #ffffff; border: 1px solid #e4e7ec; border-radius: 12px; padding: 0.9rem;
    }
    h1, h2, h3, h4 {color: #102a43;}
    </style>
    """,
    unsafe_allow_html=True,
)

data = load_portfolio()

with st.sidebar:
    st.title("Program Ops Hub")
    st.caption("Acme Cloud TPM portfolio")
    page = st.radio(
        "Navigate",
        [
            "Portfolio Dashboard",
            "Governance Review",
            "Delivery Forecasting",
            "Milestones",
            "Weekly Review Notes",
            "Decision Register",
            "Submit Update",
            "Program Details",
            "Risks",
            "Dependencies",
        ],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("MVP · Synthetic enterprise data")

views = {
    "Portfolio Dashboard": render_dashboard,
    "Governance Review": render_governance_review,
    "Delivery Forecasting": render_delivery_forecasting,
    "Milestones": render_milestones,
    "Weekly Review Notes": render_weekly_review,
    "Decision Register": render_decision_register,
    "Submit Update": render_manual_update,
    "Program Details": render_program_details,
    "Risks": render_risks,
    "Dependencies": render_dependencies,
}

views[page](data)
