"""Unit tests for hierarchy inference and graph structure validation."""

from backend.app.schemas.employee import EmployeeInput
from backend.app.schemas.hierarchy import HierarchyAnalyzeRequest
from backend.app.services.hierarchy_service import HierarchyService
from backend.app.utils.title_utils import (
    detect_cycles_in_relationships,
    validate_hierarchy_structure,
)


def test_simple_four_level_hierarchy():
    """
    Tests classic 4-level hierarchy structure:
    CEO -> VP Engineering -> Engineering Manager -> Software Engineer
    """
    service = HierarchyService()
    request = HierarchyAnalyzeRequest(
        company="TechCorp",
        employees=[
            EmployeeInput(id="1", name="Alice", title="CEO", department=None),
            EmployeeInput(id="2", name="Bob", title="VP Engineering", department="Engineering"),
            EmployeeInput(
                id="3", name="Charlie", title="Engineering Manager", department="Engineering"
            ),
            EmployeeInput(
                id="4", name="Diana", title="Software Engineer", department="Engineering"
            ),
        ],
    )

    response = service.analyze(request)

    assert response.company == "TechCorp"
    assert len(response.people) == 4
    assert response.analysis_metadata.is_valid is True

    people_map = {p.id: p for p in response.people}

    # CEO should be root
    assert people_map["1"].reports_to is None
    assert "1" in response.root_employee_ids

    # VP Engineering should report to CEO
    assert people_map["2"].reports_to == "1"

    # Engineering Manager should report to VP Engineering
    assert people_map["3"].reports_to == "2"

    # Software Engineer should report to Engineering Manager
    assert people_map["4"].reports_to == "3"


def test_cycle_detection_direct_loop():
    """Tests detection of direct 2-node cycle (A -> B -> A)."""
    relationships = [
        {"employee_id": "1", "parent_id": "2"},
        {"employee_id": "2", "parent_id": "1"},
    ]
    cycles = detect_cycles_in_relationships(relationships)
    assert len(cycles) > 0


def test_cycle_detection_three_node_loop():
    """Tests detection of 3-node cycle (A -> B -> C -> A)."""
    relationships = [
        {"employee_id": "1", "parent_id": "2"},
        {"employee_id": "2", "parent_id": "3"},
        {"employee_id": "3", "parent_id": "1"},
    ]
    cycles = detect_cycles_in_relationships(relationships)
    assert len(cycles) > 0


def test_validate_hierarchy_structure_self_reporting():
    """Tests failure when an employee reports to themselves."""
    emp_ids = {"1", "2"}
    relationships = [
        {"employee_id": "1", "parent_id": "1"},
        {"employee_id": "2", "parent_id": "1"},
    ]
    is_valid, errors, _ = validate_hierarchy_structure(emp_ids, relationships)
    assert is_valid is False
    assert any("Self-reporting" in err for err in errors)


def test_validate_hierarchy_structure_invalid_parent():
    """Tests failure when referencing a non-existent parent ID."""
    emp_ids = {"1", "2"}
    relationships = [
        {"employee_id": "1", "parent_id": "999"},
        {"employee_id": "2", "parent_id": "1"},
    ]
    is_valid, errors, _ = validate_hierarchy_structure(emp_ids, relationships)
    assert is_valid is False
    assert any("Invalid parent_id" in err for err in errors)


def test_validate_hierarchy_multiple_roots():
    """Tests valid forest containing multiple disjoint root leaders."""
    emp_ids = {"1", "2", "3", "4"}
    relationships = [
        {"employee_id": "1", "parent_id": None},  # Engineering root
        {"employee_id": "2", "parent_id": "1"},
        {"employee_id": "3", "parent_id": None},  # Sales root
        {"employee_id": "4", "parent_id": "3"},
    ]
    is_valid, errors, root_ids = validate_hierarchy_structure(emp_ids, relationships)
    assert is_valid is True
    assert len(errors) == 0
    assert set(root_ids) == {"1", "3"}
