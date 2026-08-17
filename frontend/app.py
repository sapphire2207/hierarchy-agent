"""Main Streamlit Application for Hierarchy & Buying-Role Classification Agent."""

import json
import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from frontend.components.employee_table import render_employee_table
from frontend.components.input_forms import render_input_section
from frontend.components.org_chart import render_org_chart
from frontend.components.stats_overview import render_stats_overview
from frontend.services.api_client import BackendAPIClient

# Streamlit Page Config
st.set_page_config(
    page_title="Hierarchy & Buying-Role Agent",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 4px;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #94A3B8;
        margin-bottom: 20px;
    }
    .status-badge-ok {
        background-color: #064E3B;
        color: #6EE7B7;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }
    .status-badge-err {
        background-color: #7F1D1D;
        color: #FCA5A5;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


def main():
    # Initialize session state for persistent results
    if "analysis_data" not in st.session_state:
        st.session_state["analysis_data"] = None

    # Top Header
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.markdown('<div class="main-header">🏢 Hierarchy & Buying-Role Agent</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Infer organizational structures, reporting lines, and B2B buying committee roles from employee rosters.</div>', unsafe_allow_html=True)

    # API Client
    api_url = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")
    client = BackendAPIClient(base_url=api_url)

    with header_col2:
        is_healthy, health_msg = client.check_health()
        if is_healthy:
            st.markdown(f'<div style="text-align: right;"><span class="status-badge-ok">🟢 Backend Online ({api_url})</span></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="text-align: right;"><span class="status-badge-err">🔴 Backend Offline</span></div>', unsafe_allow_html=True)
            st.caption(health_msg)

    # Sidebar Inputs
    company_name, employees, submit_clicked = render_input_section()

    # Handle Analysis Execution
    if submit_clicked:
        if not employees:
            st.error("Please provide at least one employee with a job title.")
        else:
            with st.spinner(f"🤖 LangGraph Agent is analyzing {len(employees)} employees at '{company_name}'..."):
                result, error = client.analyze_hierarchy(
                    company=company_name,
                    employees=employees,
                )

                if error:
                    st.error(f"❌ Analysis failed: {error}")
                else:
                    st.session_state["analysis_data"] = result
                    st.success(f"✨ Analysis completed successfully for **{company_name}**!")

    # Display Dashboard Results
    analysis_data = st.session_state.get("analysis_data")

    if analysis_data:
        people = analysis_data.get("people", [])
        root_ids = analysis_data.get("root_employee_ids", [])
        company = analysis_data.get("company", company_name)

        tab1, tab2, tab3, tab4 = st.tabs([
            "🌳 Interactive Org Tree",
            "👥 Buying Committee Insights",
            "📋 Employee Directory",
            "🔍 Raw JSON Inspector",
        ])

        with tab1:
            render_org_chart(people=people, root_ids=root_ids, height_px=620)

        with tab2:
            render_stats_overview(analysis_data=analysis_data)

        with tab3:
            render_employee_table(people=people, company_name=company)

        with tab4:
            st.markdown("#### 🔍 Full Backend API Response JSON")
            st.json(analysis_data)
    else:
        st.info("👈 Select a preset demo or upload a roster from the sidebar, then click **'Run Hierarchy & Buying-Role Agent'** to start.")


if __name__ == "__main__":
    main()
