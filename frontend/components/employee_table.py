"""Employee directory and export table component."""

import json
from typing import Any, Dict, List
import pandas as pd
import streamlit as st


def render_employee_table(people: List[Dict[str, Any]], company_name: str = "Company"):
    """Renders a filterable, searchable employee table with export options."""
    st.markdown("#### 📋 Analyzed Employee Directory")

    if not people:
        st.info("No employee data available.")
        return

    df = pd.DataFrame(people)

    # Manager Name lookup
    name_map = {str(p.get("id")): p.get("name") or f"Emp {p.get('id')}" for p in people}
    df["reports_to_name"] = df["reports_to"].apply(
        lambda x: f"{name_map.get(str(x))} (ID: {x})" if pd.notna(x) and str(x) in name_map else ("Top Executive (Root)" if pd.isna(x) or x is None else str(x))
    )

    # Filters
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        roles_available = ["All Roles"] + sorted(list(df["buying_role"].dropna().unique()))
        selected_role = st.selectbox("Filter by Buying Role", roles_available)

    with col_f2:
        depts_available = ["All Departments"] + sorted(list(df["department"].dropna().unique()))
        selected_dept = st.selectbox("Filter by Department", depts_available)

    with col_f3:
        search_query = st.text_input("🔍 Search Name or Title", "")

    # Apply filters
    filtered_df = df.copy()
    if selected_role != "All Roles":
        filtered_df = filtered_df[filtered_df["buying_role"] == selected_role]

    if selected_dept != "All Departments":
        filtered_df = filtered_df[filtered_df["department"] == selected_dept]

    if search_query:
        q = search_query.lower()
        filtered_df = filtered_df[
            filtered_df["name"].fillna("").str.lower().str.contains(q)
            | filtered_df["normalized_title"].fillna("").str.lower().str.contains(q)
            | filtered_df["original_title"].fillna("").str.lower().str.contains(q)
        ]

    # Select columns to display
    display_cols = [
        "id",
        "name",
        "normalized_title",
        "department",
        "seniority",
        "seniority_score",
        "buying_role",
        "confidence",
        "reports_to_name",
    ]
    display_df = filtered_df[[c for c in display_cols if c in filtered_df.columns]].rename(
        columns={
            "id": "ID",
            "name": "Name",
            "normalized_title": "Normalized Title",
            "department": "Department",
            "seniority": "Seniority",
            "seniority_score": "Score",
            "buying_role": "Buying Role",
            "confidence": "Confidence",
            "reports_to_name": "Reports To",
        }
    )

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Download Actions
    st.markdown("##### 💾 Export Results")
    down_col1, down_col2 = st.columns(2)
    with down_col1:
        csv_data = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Filtered CSV",
            data=csv_data,
            file_name=f"{company_name.lower().replace(' ', '_')}_hierarchy_analysis.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with down_col2:
        json_data = json.dumps(people, indent=2).encode("utf-8")
        st.download_button(
            label="📥 Download Full JSON Analysis",
            data=json_data,
            file_name=f"{company_name.lower().replace(' ', '_')}_hierarchy_analysis.json",
            mime="application/json",
            use_container_width=True,
        )
