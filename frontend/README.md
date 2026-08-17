# Hierarchy & Buying-Role Agent — Streamlit Frontend

An interactive, visual dashboard built with **Streamlit** to interface with the FastAPI backend agent, render hierarchical org trees color-coded by buying committee roles, and provide analytical insights.

---

## 1. Features

- **🌳 Interactive Org Tree Chart**: Hierarchical directed graph rendered with PyVis, color-coded by B2B Buying Role with hover tooltips (Title, Seniority Score, Department, Observable Reason).
- **👥 Buying Committee Insights**: Summary KPIs (Headcount, Roots, Latency), distribution breakdown, and individual rationale cards with supporting factors.
- **📥 Multiple Data Sources**:
  - **1-Click Presets**: Acme Technologies, NovaPay Financial, Aether AI Cloud, OmniRetail Global.
  - **CSV / Excel Uploader**: Automated column mapping for rosters.
  - **JSON Editor**: Paste or customize raw payloads.
- **📋 Searchable Employee Directory**: Real-time filtering by Role and Department, with **CSV & JSON download** buttons.
- **🟢 Live Backend Health Indicator**: Real-time connectivity check with the FastAPI backend.

---

## 2. Quickstart

### Step 1: Ensure Backend is Running
In one terminal, make sure your FastAPI backend server is active:
```powershell
.\backend\.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload --port 8000
```

### Step 2: Activate the Frontend Virtual Environment
In a second terminal:
```powershell
.\frontend\.venv\Scripts\Activate.ps1
```

*(On Linux / macOS: `source frontend/.venv/bin/activate`)*

### Step 3: Run the Streamlit Application
```powershell
streamlit run frontend/app.py
```

The app will automatically open in your default browser at:
`http://localhost:8501`

---

## 3. Directory Structure

```text
frontend/
├── app.py                      # Main Streamlit application
├── components/
│   ├── input_forms.py          # Preset datasets selector, CSV uploader, JSON editor
│   ├── org_chart.py            # Interactive Tree / Network Graph visualization
│   ├── stats_overview.py       # Metrics and buying committee cards
│   └── employee_table.py       # Searchable directory with export buttons
├── services/
│   └── api_client.py           # Backend HTTP client & health check
├── requirements.txt            # Frontend dependencies
├── .env.example                # Config (BACKEND_API_URL=http://127.0.0.1:8000)
└── README.md
```
