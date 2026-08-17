"""Stats overview and Buying Committee breakdown component."""

from collections import Counter
from typing import Any, Dict, List
import streamlit as st

from frontend.components.org_chart import ROLE_COLORS, ROLE_EMOJIS


def render_stats_overview(analysis_data: Dict[str, Any]):
    """Renders KPI metrics and buying committee role cards."""
    metadata = analysis_data.get("analysis_metadata", {})
    people = analysis_data.get("people", [])
    company = analysis_data.get("company", "Company")

    st.markdown(f"### 📊 Buying Committee Insights & Overview — **{company}**")

    # Top KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Total Headcount", value=metadata.get("total_employees", len(people)))
    with col2:
        st.metric(label="Org Roots / Branches", value=metadata.get("root_count", len(analysis_data.get("root_employee_ids", []))))
    with col3:
        latency = metadata.get("execution_time_ms")
        st.metric(label="Analysis Latency", value=f"{latency:.1f} ms" if latency is not None else "N/A")
    with col4:
        is_valid = metadata.get("is_valid", True)
        st.metric(label="Graph Structure", value="✅ Valid Tree" if is_valid else "⚠️ Has Warnings")

    st.markdown("---")

    # Role Distribution Count
    role_counts = Counter(p.get("buying_role", "Unknown") for p in people)

    st.markdown("#### 👥 Buying Committee Role Distribution")
    role_cols = st.columns(5)
    target_roles = ["Economic Buyer", "Champion", "Influencer", "User", "Unknown"]

    for idx, role_name in enumerate(target_roles):
        with role_cols[idx]:
            count = role_counts.get(role_name, 0)
            emoji = ROLE_EMOJIS.get(role_name, "")
            color_cfg = ROLE_COLORS.get(role_name, ROLE_COLORS["Unknown"])
            st.markdown(
                f"""
                <div style="background-color: {color_cfg['background']}22; border-left: 4px solid {color_cfg['border']}; padding: 10px; border-radius: 6px; margin-bottom: 8px;">
                    <div style="font-size: 12px; color: #94A3B8; text-transform: uppercase;">{emoji} {role_name}</div>
                    <div style="font-size: 24px; font-weight: 700; color: #F8FAFC;">{count}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("#### 🎯 Role Justifications & Decision Factors")

    # Grouped Cards by Role
    for role_name in target_roles:
        matched_people = [p for p in people if p.get("buying_role") == role_name]
        if not matched_people:
            continue

        emoji = ROLE_EMOJIS.get(role_name, "")
        with st.expander(f"{emoji} **{role_name}s** ({len(matched_people)})", expanded=(role_name in ["Economic Buyer", "Champion"])):
            for p in matched_people:
                name = p.get("name") or f"Employee {p.get('id')}"
                norm_title = p.get("normalized_title") or p.get("original_title")
                dept = p.get("department") or "General"
                conf = float(p.get("confidence", 0.5))
                reason = p.get("reason", "")
                factors = p.get("supporting_factors", [])
                score = p.get("seniority_score", 0)

                factors_badge_html = " ".join(
                    f"<span style='background-color: #334155; padding: 2px 8px; border-radius: 12px; font-size: 11px; margin-right: 4px;'>{f}</span>"
                    for f in factors
                )

                st.markdown(
                    f"""
                    <div style="background: #1E293B; border-radius: 8px; padding: 12px; margin-bottom: 10px; border: 1px solid #334155;">
                        <div style="display: flex; justify-content: space-between; align-items: baseline;">
                            <span style="font-weight: 600; font-size: 15px; color: #F8FAFC;">{name} — <span style="color: #94A3B8; font-weight: 400;">{norm_title}</span></span>
                            <span style="font-size: 12px; color: #38BDF8; font-weight: 600;">Confidence: {int(conf * 100)}%</span>
                        </div>
                        <div style="font-size: 13px; color: #CBD5E1; margin-top: 6px;">{reason}</div>
                        <div style="margin-top: 8px; font-size: 12px; color: #94A3B8;">
                            <b>Dept:</b> {dept} | <b>Seniority Score:</b> {score}/10 | <b>Factors:</b> {factors_badge_html if factors_badge_html else 'N/A'}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
