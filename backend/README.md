# Hierarchy & Buying-Role Classification Agent (Backend)

A production-oriented backend MVP that infers corporate organizational hierarchies and classifies employees into B2B buying committee roles using Python, FastAPI, LangGraph, LangChain, Pydantic, and structured LLM outputs.

---

## 1. System Architecture

```text
FastAPI (POST /api/v1/hierarchy/analyze)
   ↓
Hierarchy Service
   ↓
LangGraph Workflow
   ↓
[validate_input] ───────── (deterministic input sanitizer & validation)
   ↓
[normalize_titles] ─────── (deterministic rules + LLM standardization)
   ↓
[extract_attributes] ───── (seniority scoring 0-10, function, mgmt levels)
   ↓
[build_hierarchy] ──────── (global tree inference with cycle prevention)
   ↓
[classify_roles] ───────── (B2B buying role classification with confidence)
   ↓
[validate_results] ─────── (graph cycle check & structural audit, max retries)
   ↓
[compile_final_output] ─── (produces clean FinalHierarchyResponse)
```

---

## 2. Buying Committee Taxonomy

The agent classifies employees into exactly one of five permitted B2B buying roles:

| Role | Definition | Typical Profiles |
| :--- | :--- | :--- |
| **Economic Buyer** | Holds budget ownership, financial sign-off, or final purchasing authority. | CFO, VP Finance, CEO, Business Unit Head |
| **Champion** | Internal advocate who benefits from the tool and mobilizes stakeholders. | VP Engineering, Director of Product |
| **Influencer** | Shapes technical requirements, security/compliance, or procurement. | CTO, Security Architect, Procurement Manager |
| **User** | Direct hands-on practitioner who uses the product in daily workflows. | Senior Software Engineer, Data Analyst |
| **Unknown** | Context or title is too ambiguous to assign a role with confidence. | Generic titles with missing context |

---

## 3. Installation & Setup

### Prerequisites
- Python 3.12+ (Python 3.13 supported)

### Step 1: Create and Activate Virtual Environment
```bash
# On Windows (PowerShell)
.\backend\.venv\Scripts\Activate.ps1

# On Linux/macOS
source backend/.venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env` in the project root:
```bash
cp backend/.env.example .env
```

Key environment configuration variables:
```dotenv
APP_NAME="Hierarchy & Buying-Role Classification Agent"
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO

# LLM Provider: 'mock' (offline/tests), 'openai', 'google_genai', 'anthropic', 'groq', 'ollama'
LLM_PROVIDER=mock
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=
LLM_BASE_URL=
LLM_TEMPERATURE=0.0

MAX_RETRIES=2
GRAPH_TIMEOUT_SECONDS=60
```

---

## 4. Running the Server

Start the development server with Uvicorn:

```bash
uvicorn backend.app.main:app --reload --port 8000
```

Interactive API documentation (Swagger UI) is available at:
`http://127.0.0.1:8000/docs`

---

## 5. API Documentation

### 5.1 Health Check
**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "ok"
}
```

---

### 5.2 Analyze Hierarchy & Buying Roles
**Endpoint**: `POST /api/v1/hierarchy/analyze`

**Request Body**:
```json
{
  "company": "Acme Technologies",
  "employees": [
    {
      "id": "1",
      "name": "John",
      "title": "CEO",
      "department": null
    },
    {
      "id": "2",
      "name": "Sarah",
      "title": "CFO",
      "department": "Finance"
    },
    {
      "id": "3",
      "name": "David",
      "title": "CTO",
      "department": "Technology"
    },
    {
      "id": "4",
      "name": "Emily",
      "title": "VP Engineering",
      "department": "Engineering"
    },
    {
      "id": "5",
      "name": "Mike",
      "title": "Director of Engineering",
      "department": "Engineering"
    },
    {
      "id": "6",
      "name": "Alex",
      "title": "Engineering Manager",
      "department": "Engineering"
    },
    {
      "id": "7",
      "name": "Robert",
      "title": "Senior Software Engineer",
      "department": "Engineering"
    },
    {
      "id": "8",
      "name": "James",
      "title": "Software Engineer",
      "department": "Engineering"
    },
    {
      "id": "9",
      "name": "Lisa",
      "title": "Procurement Manager",
      "department": "Procurement"
    }
  ]
}
```

**Example Response**:
```json
{
  "company": "Acme Technologies",
  "people": [
    {
      "id": "1",
      "name": "John",
      "original_title": "CEO",
      "normalized_title": "Chief Executive Officer",
      "department": "Executive",
      "function": "Executive Leadership",
      "seniority": "C-Level",
      "seniority_score": 10,
      "management_level": "Executive",
      "reports_to": null,
      "buying_role": "Economic Buyer",
      "confidence": 0.8,
      "reason": "Executive leadership with overarching commercial sign-off and strategic decision ownership.",
      "supporting_factors": ["Executive Leadership", "Final Decision Authority"]
    },
    {
      "id": "2",
      "name": "Sarah",
      "original_title": "CFO",
      "normalized_title": "Chief Financial Officer",
      "department": "Finance",
      "function": "Executive Leadership",
      "seniority": "C-Level",
      "seniority_score": 10,
      "management_level": "Executive",
      "reports_to": "1",
      "buying_role": "Economic Buyer",
      "confidence": 0.92,
      "reason": "Controls organizational budget, financial authorizations, and final purchasing commitments.",
      "supporting_factors": ["Financial Oversight", "Executive Budget Authority", "Sign-off Responsibility"]
    },
    {
      "id": "4",
      "name": "Emily",
      "original_title": "VP Engineering",
      "normalized_title": "Vice President of Engineering",
      "department": "Engineering",
      "function": "Engineering Management",
      "seniority": "VP",
      "seniority_score": 8,
      "management_level": "Executive",
      "reports_to": "1",
      "buying_role": "Champion",
      "confidence": 0.89,
      "reason": "Senior domain leader who actively champions tools that improve departmental productivity and efficiency.",
      "supporting_factors": ["Departmental Leadership", "Operational Alignment", "Internal Influence"]
    },
    {
      "id": "7",
      "name": "Robert",
      "original_title": "Senior Software Engineer",
      "normalized_title": "Senior Software Engineer",
      "department": "Engineering",
      "function": "Software Development",
      "seniority": "Senior",
      "seniority_score": 3,
      "management_level": "Individual Contributor",
      "reports_to": "6",
      "buying_role": "User",
      "confidence": 0.82,
      "reason": "Hands-on technical contributor who will directly interact with and utilize the tooling daily.",
      "supporting_factors": ["Hands-on Practitioner", "Daily Workflow Consumer", "Direct End User"]
    }
  ],
  "root_employee_ids": ["1"],
  "analysis_metadata": {
    "total_employees": 9,
    "root_count": 1,
    "execution_time_ms": 14.85,
    "retry_count": 0,
    "is_valid": true,
    "warnings": []
  }
}
```

---

## 6. Testing & Code Quality

Run the test suite with Pytest:
```bash
pytest -v
```

Run code formatting and lint checks with Ruff:
```bash
ruff check backend/
ruff format backend/
```
