# Hierarchy & Buying-Role Classification Agent

An enterprise-ready AI system for inferring corporate reporting hierarchies and classifying employees into B2B buying committee roles from employee title rosters.

Built with **Python 3.13**, **FastAPI**, **LangGraph**, **LangChain**, **Pydantic**, and an interactive **Streamlit Frontend**.

---

## 1. System Overview

B2B sales and RevOps teams regularly receive lists of contact names and job titles from target accounts. This system analyzes employee rosters to:
1. Standardize and normalize abbreviated or informal job titles.
2. Extract rich organizational attributes (seniority taxonomy, seniority score 0-10, functional area, management status).
3. Holistically infer organizational reporting trees (or disjoint forests) with cycle detection and validation.
4. Classify each contact into a standard B2B buying role (`Economic Buyer`, `Champion`, `Influencer`, `User`, `Unknown`) with confidence ratings and concise, observable evidence.
5. Render an interactive, color-coded organizational graph and buying committee breakdown in the Streamlit UI.

---

## 2. Directory Structure

```text
hierarchy-agent/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/hierarchy.py       # POST /api/v1/hierarchy/analyze
│   │   ├── core/
│   │   │   ├── config.py                 # Pydantic BaseSettings
│   │   │   └── logging.py                # Structured logging configuration
│   │   ├── schemas/                      # Strongly typed Pydantic models
│   │   ├── agents/                       # LangGraph StateGraph & nodes
│   │   ├── services/                     # Hierarchy service & multi-provider LLM
│   │   ├── utils/                        # Deterministic normalization & graph cycle checks
│   │   └── main.py                       # FastAPI entry point & GET /health
│   │
│   ├── tests/                            # 16 unit & integration tests
│   ├── requirements.txt                  # Backend dependencies
│   ├── .env.example
│   └── README.md
│
├── frontend/
│   ├── app.py                            # Streamlit dashboard entry point
│   ├── components/                       # Org chart, KPI stats, directory table, input forms
│   ├── services/                         # Backend API client
│   ├── requirements.txt                  # Frontend dependencies
│   ├── .env.example
│   └── README.md
│
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## 3. How to Run

### Terminal 1: Start Backend (FastAPI)
```powershell
.\backend\.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload --port 8000
```
- API Health Check: `http://localhost:8000/health`
- Swagger API Docs: `http://localhost:8000/docs`

### Terminal 2: Start Frontend (Streamlit)
```powershell
.\frontend\.venv\Scripts\Activate.ps1
streamlit run frontend/app.py
```
- Open in Browser: `http://localhost:8501`
