"""Interactive Org Chart visualization component using PyVis and Streamlit."""

from typing import Any, Dict, List
from pyvis.network import Network
import streamlit.components.v1 as components
import streamlit as st

ROLE_COLORS = {
    "Economic Buyer": {"background": "#10B981", "border": "#047857", "highlight": "#34D399"},
    "Champion": {"background": "#3B82F6", "border": "#1D4ED8", "highlight": "#60A5FA"},
    "Influencer": {"background": "#8B5CF6", "border": "#6D28D9", "highlight": "#A78BFA"},
    "User": {"background": "#F59E0B", "border": "#B45309", "highlight": "#FBBF24"},
    "Unknown": {"background": "#6B7280", "border": "#374151", "highlight": "#9CA3AF"},
}

ROLE_EMOJIS = {
    "Economic Buyer": "💰",
    "Champion": "⭐",
    "Influencer": "🧠",
    "User": "💻",
    "Unknown": "❓",
}


def render_org_chart(people: List[Dict[str, Any]], root_ids: List[str], height_px: int = 600):
    """
    Renders an interactive hierarchical organization tree using PyVis.
    Nodes are color-coded by B2B buying role.
    """
    st.markdown("#### 🌳 Interactive Organizational Reporting Tree")

    # Legend
    legend_html = """
    <div style="display: flex; flex-wrap: wrap; gap: 14px; margin-bottom: 12px; font-size: 13px; font-weight: 500;">
        <span style="display: inline-flex; align-items: center; gap: 6px;">
            <span style="width: 14px; height: 14px; background-color: #10B981; border-radius: 4px; display: inline-block;"></span> 💰 Economic Buyer
        </span>
        <span style="display: inline-flex; align-items: center; gap: 6px;">
            <span style="width: 14px; height: 14px; background-color: #3B82F6; border-radius: 4px; display: inline-block;"></span> ⭐ Champion
        </span>
        <span style="display: inline-flex; align-items: center; gap: 6px;">
            <span style="width: 14px; height: 14px; background-color: #8B5CF6; border-radius: 4px; display: inline-block;"></span> 🧠 Influencer
        </span>
        <span style="display: inline-flex; align-items: center; gap: 6px;">
            <span style="width: 14px; height: 14px; background-color: #F59E0B; border-radius: 4px; display: inline-block;"></span> 💻 User
        </span>
        <span style="display: inline-flex; align-items: center; gap: 6px;">
            <span style="width: 14px; height: 14px; background-color: #6B7280; border-radius: 4px; display: inline-block;"></span> ❓ Unknown
        </span>
    </div>
    """
    st.markdown(legend_html, unsafe_allow_html=True)

    net = Network(
        height=f"{height_px}px",
        width="100%",
        directed=True,
        bgcolor="#0F172A",
        font_color="#F8FAFC",
    )

    # Configure physics for hierarchical tree layout
    net.set_options("""
    {
      "layout": {
        "hierarchical": {
          "enabled": true,
          "direction": "UD",
          "sortMethod": "directed",
          "nodeSpacing": 180,
          "levelSeparation": 130,
          "treeSpacing": 200
        }
      },
      "nodes": {
        "shape": "box",
        "margin": 10,
        "shadow": true,
        "font": {
          "size": 13,
          "face": "Inter, system-ui, sans-serif",
          "color": "#FFFFFF"
        }
      },
      "edges": {
        "arrows": {
          "to": { "enabled": true, "scaleFactor": 0.8 }
        },
        "color": { "color": "#475569", "highlight": "#60A5FA" },
        "smooth": { "type": "cubicBezier", "forceDirection": "vertical" }
      },
      "physics": {
        "hierarchicalRepulsion": {
          "nodeDistance": 180
        }
      },
      "interaction": {
        "hover": true,
        "dragNodes": true,
        "zoomView": true
      }
    }
    """)

    # Add Nodes
    for person in people:
        p_id = str(person.get("id"))
        name = person.get("name") or f"Employee {p_id}"
        norm_title = person.get("normalized_title", person.get("original_title", "Unknown Title"))
        dept = person.get("department") or "General"
        score = person.get("seniority_score", 0)
        mgmt = person.get("management_level", "")
        role = person.get("buying_role", "Unknown")
        conf = float(person.get("confidence", 0.5))
        reason = person.get("reason", "")
        emoji = ROLE_EMOJIS.get(role, "")

        color_cfg = ROLE_COLORS.get(role, ROLE_COLORS["Unknown"])

        label = f"{name}\n{norm_title}\n[{emoji} {role}]"

        tooltip = f"""
        <b>{name}</b> ({dept})<br/>
        <b>Title:</b> {norm_title}<br/>
        <b>Seniority Score:</b> {score}/10 ({mgmt})<br/>
        <b>Buying Role:</b> {role} (Confidence: {int(conf*100)}%)<br/>
        <b>Rationale:</b> {reason}
        """

        net.add_node(
            n_id=p_id,
            label=label,
            title=tooltip,
            color={
                "background": color_cfg["background"],
                "border": color_cfg["border"],
                "highlight": {
                    "background": color_cfg["highlight"],
                    "border": color_cfg["border"],
                },
            },
            shape="box",
        )

    # Add Edges (Parent -> Child for intuitive top-down hierarchy flow)
    for person in people:
        p_id = str(person.get("id"))
        parent_id = person.get("reports_to")

        if parent_id is not None:
            parent_id_str = str(parent_id)
            # Edge from manager (parent) -> direct report (child)
            net.add_edge(
                source=parent_id_str,
                to=p_id,
                title=f"Manages {person.get('name') or p_id}",
            )

    html_content = net.generate_html()
    components.html(html_content, height=height_px + 20, scrolling=True)
