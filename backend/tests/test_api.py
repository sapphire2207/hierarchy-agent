"""API endpoint tests using FastAPI TestClient."""

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Tests GET /health returns 200 OK and status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_v1_health_endpoint():
    """Tests GET /api/v1/health returns 200 OK and status ok."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_hierarchy_acme_technologies_test_case():
    """
    Tests the official Section 26 initial dataset with 9 employees at Acme Technologies.
    """
    payload = {
        "company": "Acme Technologies",
        "employees": [
            {"id": "1", "name": "John", "title": "CEO", "department": None},
            {"id": "2", "name": "Sarah", "title": "CFO", "department": "Finance"},
            {"id": "3", "name": "David", "title": "CTO", "department": "Technology"},
            {"id": "4", "name": "Emily", "title": "VP Engineering", "department": "Engineering"},
            {
                "id": "5",
                "name": "Mike",
                "title": "Director of Engineering",
                "department": "Engineering",
            },
            {
                "id": "6",
                "name": "Alex",
                "title": "Engineering Manager",
                "department": "Engineering",
            },
            {
                "id": "7",
                "name": "Robert",
                "title": "Senior Software Engineer",
                "department": "Engineering",
            },
            {"id": "8", "name": "James", "title": "Software Engineer", "department": "Engineering"},
            {
                "id": "9",
                "name": "Lisa",
                "title": "Procurement Manager",
                "department": "Procurement",
            },
        ],
    }

    response = client.post("/api/v1/hierarchy/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["company"] == "Acme Technologies"
    assert len(data["people"]) == 9
    assert data["analysis_metadata"]["is_valid"] is True
    assert data["analysis_metadata"]["total_employees"] == 9
    assert "1" in data["root_employee_ids"]

    # Verify structural integrity
    people_by_id = {p["id"]: p for p in data["people"]}

    assert people_by_id["1"]["normalized_title"] == "Chief Executive Officer"
    assert people_by_id["1"]["seniority_score"] == 10
    assert people_by_id["1"]["reports_to"] is None

    assert people_by_id["4"]["normalized_title"] == "Vice President of Engineering"
    assert people_by_id["4"]["seniority_score"] == 8

    # Check that all roles and confidence are well-formed
    for person in data["people"]:
        assert person["buying_role"] in [
            "Economic Buyer",
            "Champion",
            "Influencer",
            "User",
            "Unknown",
        ]
        assert 0.0 <= person["confidence"] <= 1.0
        assert len(person["reason"]) > 0
        assert isinstance(person["supporting_factors"], list)


def test_analyze_hierarchy_minimal_payload():
    """Tests analysis with only id and title (names and departments omitted)."""
    payload = {
        "employees": [
            {"id": "101", "title": "VP Engineering"},
            {"id": "102", "title": "Senior Software Engineer"},
        ]
    }

    response = client.post("/api/v1/hierarchy/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert len(data["people"]) == 2
    assert data["analysis_metadata"]["is_valid"] is True


def test_analyze_hierarchy_empty_employees_validation_error():
    """Tests validation error when employees list is empty."""
    payload = {"company": "Empty Corp", "employees": []}
    response = client.post("/api/v1/hierarchy/analyze", json=payload)
    assert response.status_code == 422


def test_analyze_hierarchy_duplicate_ids_validation_error():
    """Tests validation error when employee IDs are duplicated."""
    payload = {
        "company": "Duplicate Corp",
        "employees": [
            {"id": "1", "title": "CEO"},
            {"id": "1", "title": "VP Engineering"},
        ],
    }
    response = client.post("/api/v1/hierarchy/analyze", json=payload)
    assert response.status_code == 422


def test_analyze_hierarchy_empty_title_validation_error():
    """Tests validation error when job title is empty or blank spaces."""
    payload = {
        "company": "Blank Corp",
        "employees": [
            {"id": "1", "title": "   "},
        ],
    }
    response = client.post("/api/v1/hierarchy/analyze", json=payload)
    assert response.status_code == 422
