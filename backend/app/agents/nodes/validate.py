"""Validation nodes for input data and final hierarchy graph structure."""

from typing import Any

from backend.app.agents.state import HierarchyState
from backend.app.core.logging import logger
from backend.app.schemas.classification import BuyingRole
from backend.app.utils.title_utils import validate_hierarchy_structure


def validate_input_node(state: HierarchyState) -> dict[str, Any]:
    """
    Deterministic input validation node.
    Validates employee existence, ID uniqueness, and non-empty titles.
    Sanitizes strings and initializes error state.
    """
    logger.info("Executing validate_input node")
    raw_employees = state.get("employees", [])
    errors: list[str] = list(state.get("errors", []))
    cleaned_employees: list[dict[str, Any]] = []

    if not raw_employees:
        errors.append("Employee list cannot be empty.")
        return {
            "employees": [],
            "errors": errors,
            "validation_results": {"is_valid": False, "errors": errors},
        }

    seen_ids: set[str] = set()
    for idx, emp in enumerate(raw_employees):
        emp_id = str(emp.get("id", "")).strip()
        if not emp_id:
            emp_id = f"emp_{idx + 1}"

        if emp_id in seen_ids:
            errors.append(f"Duplicate employee ID detected: '{emp_id}'.")
        seen_ids.add(emp_id)

        raw_title = str(emp.get("title", "")).strip()
        if not raw_title:
            errors.append(f"Employee ID '{emp_id}' has an empty or missing title.")

        raw_name = emp.get("name")
        cleaned_name = str(raw_name).strip() if raw_name else None

        raw_dept = emp.get("department")
        cleaned_dept = str(raw_dept).strip() if raw_dept else None

        cleaned_employees.append(
            {
                "id": emp_id,
                "name": cleaned_name,
                "title": raw_title,
                "department": cleaned_dept,
            }
        )

    is_valid = len(errors) == 0
    return {
        "employees": cleaned_employees,
        "errors": errors,
        "validation_results": {"is_valid": is_valid, "errors": errors},
        "retry_count": state.get("retry_count", 0),
    }


def validate_results_node(state: HierarchyState) -> dict[str, Any]:
    """
    Validates final hierarchy tree structure, buying-role integrity, and confidence scores.
    """
    logger.info("Executing validate_results node")
    employees = state.get("employees", [])
    relationships = state.get("hierarchy_relationships", [])
    roles = state.get("role_classifications", [])
    current_retry = state.get("retry_count", 0)
    errors: list[str] = []
    warnings: list[str] = []

    emp_ids: set[str] = {str(e.get("id")) for e in employees}

    # 1. Structural graph validation
    _is_valid_structure, graph_errors, root_ids = validate_hierarchy_structure(
        employee_ids=emp_ids,
        relationships=relationships,
    )
    errors.extend(graph_errors)

    # 2. Buying role validation
    valid_roles = {r.value for r in BuyingRole}
    classified_ids = set()

    for role_item in roles:
        emp_id = str(role_item.get("employee_id", ""))
        raw_role = role_item.get("buying_role")
        role_val = raw_role.value if hasattr(raw_role, "value") else str(raw_role)
        conf = float(role_item.get("confidence", 0.0))

        classified_ids.add(emp_id)

        if role_val not in valid_roles:
            errors.append(f"Invalid buying role '{role_val}' for employee ID '{emp_id}'.")

        if not (0.0 <= conf <= 1.0):
            errors.append(
                f"Confidence score {conf} out of bounds [0.0, 1.0] for employee ID '{emp_id}'."
            )

    missing_roles = emp_ids - classified_ids
    if missing_roles:
        errors.append(f"Missing buying role classifications for employees: {sorted(missing_roles)}")

    # 3. Semantic consistency checks (logged as warnings)
    norm_map = {str(e.get("id")): e for e in state.get("normalized_employees", [])}
    for role_item in roles:
        emp_id = str(role_item.get("employee_id", ""))
        raw_role = role_item.get("buying_role")
        role_val = raw_role.value if hasattr(raw_role, "value") else str(raw_role)
        emp_info = norm_map.get(emp_id, {})
        score = emp_info.get("seniority_score", 0)

        # e.g., CEO classified as User is unusual
        if score == 10 and role_val == BuyingRole.USER.value:
            warnings.append(
                f"Employee ID '{emp_id}' ({emp_info.get('normalized_title')}) has top executive seniority (10) but was classified as '{role_val}'."
            )

    is_valid = len(errors) == 0
    new_retry_count = current_retry if is_valid else current_retry + 1

    return {
        "errors": errors,
        "retry_count": new_retry_count,
        "validation_results": {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "root_employee_ids": root_ids,
        },
    }
