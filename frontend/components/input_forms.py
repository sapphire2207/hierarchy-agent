"""Input forms, CSV/JSON parser, and preset datasets for Streamlit frontend."""

import json
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import streamlit as st

PRESET_DATASETS: Dict[str, Dict[str, Any]] = {
    "Acme Technologies (Tech / Engineering Ladder)": {
        "company": "Acme Technologies",
        "employees": [
            {"id": "1", "name": "John", "title": "CEO", "department": None},
            {"id": "2", "name": "Sarah", "title": "CFO", "department": "Finance"},
            {"id": "3", "name": "David", "title": "CTO", "department": "Technology"},
            {"id": "4", "name": "Emily", "title": "VP Engineering", "department": "Engineering"},
            {"id": "5", "name": "Mike", "title": "Director of Engineering", "department": "Engineering"},
            {"id": "6", "name": "Alex", "title": "Engineering Manager", "department": "Engineering"},
            {"id": "7", "name": "Robert", "title": "Senior Software Engineer", "department": "Engineering"},
            {"id": "8", "name": "James", "title": "Software Engineer", "department": "Engineering"},
            {"id": "9", "name": "Lisa", "title": "Procurement Manager", "department": "Procurement"},
        ],
    },
    "NovaPay Financial (SaaS / FinTech Scale-up)": {
        "company": "NovaPay Financial",
        "employees": [
            {"id": "NP-01", "name": "Marcus Vance", "title": "Chief Executive Officer", "department": "Executive"},
            {"id": "NP-02", "name": "Elena Rostova", "title": "VP of Product Management", "department": "Product"},
            {"id": "NP-03", "name": "Liam Chen", "title": "Lead Product Designer", "department": "Product"},
            {"id": "NP-04", "name": "Priya Sharma", "title": "Chief Information Security Officer", "department": "Security"},
            {"id": "NP-05", "name": "Carlos Gomez", "title": "Head of Growth Marketing", "department": "Marketing"},
            {"id": "NP-06", "name": "Hannah Abbott", "title": "Senior Growth Marketing Analyst", "department": "Marketing"},
            {"id": "NP-07", "name": "Zack Taylor", "title": "Vice President of Finance", "department": "Finance"},
        ],
    },
    "Aether AI Cloud (AI & Infrastructure)": {
        "company": "Aether AI Cloud",
        "employees": [
            {"id": "AI-101", "name": "Dr. Aris Thorne", "title": "President & CTO", "department": "Technology"},
            {"id": "AI-102", "name": "Sophia Lin", "title": "Senior Director of Infrastructure & SRE", "department": "Infrastructure"},
            {"id": "AI-103", "name": "Dmitri Volkov", "title": "Principal Cloud Architect", "department": "Infrastructure"},
            {"id": "AI-104", "name": "Amina Al-Mansoor", "title": "Site Reliability Engineering Manager", "department": "Infrastructure"},
            {"id": "AI-105", "name": "Jordan Bell", "title": "DevOps Engineer", "department": "Infrastructure"},
            {"id": "AI-106", "name": "Rachel Green", "title": "Global Procurement & Vendor Relations Lead", "department": "Procurement"},
        ],
    },
    "OmniRetail Global (E-Commerce & Logistics)": {
        "company": "OmniRetail Global",
        "employees": [
            {"id": "OM-501", "name": "Arthur Pendelton", "title": "Chief Operating Officer", "department": "Operations"},
            {"id": "OM-502", "name": "Beatrice Wong", "title": "Director of Supply Chain & Logistics", "department": "Supply Chain"},
            {"id": "OM-503", "name": "Samuel Jackson", "title": "Warehouse Logistics Manager", "department": "Supply Chain"},
            {"id": "OM-504", "name": "Chloe Bennett", "title": "Inventory Control Specialist", "department": "Supply Chain"},
            {"id": "OM-505", "name": "Victor Rossi", "title": "Chief Revenue Officer", "department": "Sales"},
            {"id": "OM-506", "name": "Maya Lin", "title": "Enterprise Account Executive", "department": "Sales"},
        ],
    },
}


def parse_csv_to_employees(df: pd.DataFrame) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """Normalizes uploaded DataFrame columns and returns employee payload."""
    col_map = {}
    for col in df.columns:
        c_clean = str(col).strip().lower()
        if c_clean in ["id", "emp_id", "employee_id", "user_id"]:
            col_map["id"] = col
        elif c_clean in ["name", "full_name", "employee_name", "contact_name"]:
            col_map["name"] = col
        elif c_clean in ["title", "job_title", "role", "position"]:
            col_map["title"] = col
        elif c_clean in ["department", "dept", "org", "division", "team"]:
            col_map["department"] = col

    if "title" not in col_map:
        return None, "CSV must contain a 'title' or 'job_title' column."

    employees: List[Dict[str, Any]] = []
    seen_ids = set()

    for idx, row in df.iterrows():
        emp_id = str(row[col_map["id"]]).strip() if "id" in col_map and pd.notna(row[col_map["id"]]) else str(idx + 1)
        if not emp_id or emp_id in seen_ids:
            emp_id = f"emp_{idx + 1}"
        seen_ids.add(emp_id)

        title = str(row[col_map["title"]]).strip() if pd.notna(row[col_map["title"]]) else ""
        if not title or title.lower() == "nan":
            continue

        name = str(row[col_map["name"]]).strip() if "name" in col_map and pd.notna(row[col_map["name"]]) else None
        if name and name.lower() == "nan":
            name = None

        dept = str(row[col_map["department"]]).strip() if "department" in col_map and pd.notna(row[col_map["department"]]) else None
        if dept and dept.lower() == "nan":
            dept = None

        employees.append({
            "id": emp_id,
            "name": name,
            "title": title,
            "department": dept,
        })

    if not employees:
        return None, "No valid employee rows with non-empty titles found in CSV."

    return employees, None


def render_input_section() -> Tuple[str, List[Dict[str, Any]], bool]:
    """
    Renders input options (Presets, CSV Upload, JSON Paste) in Streamlit.
    Returns (company_name, employees_list, is_submit_clicked).
    """
    st.sidebar.markdown("### 📥 Input Data Source")
    input_mode = st.sidebar.radio(
        "Choose Input Method",
        ["✨ Preset Demos", "📁 Upload CSV / Excel", "📝 Paste JSON / Text"],
        index=0,
    )

    company_name = "Company"
    employees: List[Dict[str, Any]] = []

    if input_mode == "✨ Preset Demos":
        selected_preset_name = st.sidebar.selectbox("Select Preset Roster", list(PRESET_DATASETS.keys()))
        preset_data = PRESET_DATASETS[selected_preset_name]
        company_name = st.sidebar.text_input("Company Name", value=preset_data["company"])
        employees = preset_data["employees"]

        with st.expander("👁️ View Selected Preset Roster Data", expanded=False):
            st.dataframe(pd.DataFrame(employees), use_container_width=True)

    elif input_mode == "📁 Upload CSV / Excel":
        company_name = st.sidebar.text_input("Company Name", value="Uploaded Company")
        uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel File", type=["csv", "xlsx", "xls"])

        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)

                parsed_employees, err = parse_csv_to_employees(df)
                if err:
                    st.sidebar.error(err)
                else:
                    employees = parsed_employees or []
                    st.sidebar.success(f"Loaded {len(employees)} employees from file.")
                    with st.expander("📄 Preview Uploaded Roster", expanded=False):
                        st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.sidebar.error(f"Error reading file: {e}")

    elif input_mode == "📝 Paste JSON / Text":
        company_name = st.sidebar.text_input("Company Name", value="Custom Enterprise")
        default_json = json.dumps(PRESET_DATASETS["Acme Technologies (Tech / Engineering Ladder)"]["employees"], indent=2)
        json_str = st.text_area("Paste Employee JSON Array", value=default_json, height=220)

        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, list):
                employees = parsed
            elif isinstance(parsed, dict) and "employees" in parsed:
                employees = parsed["employees"]
                if "company" in parsed and parsed["company"]:
                    company_name = parsed["company"]
        except Exception as e:
            st.warning(f"Invalid JSON format: {e}")

    submit_clicked = st.sidebar.button(
        "🚀 Run Hierarchy & Buying-Role Agent",
        type="primary",
        use_container_width=True,
        disabled=(len(employees) == 0),
    )

    return company_name, employees, submit_clicked
