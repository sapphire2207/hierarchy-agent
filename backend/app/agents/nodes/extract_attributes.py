"""Node for extracting and enriching employee attributes."""

from typing import Any

from backend.app.agents.state import HierarchyState
from backend.app.core.logging import logger
from backend.app.utils.title_utils import (
    SENIORITY_SCORES,
    extract_seniority_info,
    infer_department_and_function,
)


def extract_attributes_node(state: HierarchyState) -> dict[str, Any]:
    """
    Enriches each employee with department, functional domain, seniority taxonomy,
    numeric seniority score (0-10), and management level status.
    """
    logger.info("Executing extract_attributes node")
    normalized_employees = state.get("normalized_employees", [])
    raw_employees = {str(e.get("id")): e for e in state.get("employees", [])}

    enriched_attributes: list[dict[str, Any]] = []
    updated_normalized: list[dict[str, Any]] = []

    for item in normalized_employees:
        emp_id = str(item.get("id"))
        raw_info = raw_employees.get(emp_id, {})
        norm_title = item.get("normalized_title") or item.get("title", "")
        raw_dept = raw_info.get("department") or item.get("department")

        # Re-verify seniority & management level
        seniority, score, mgmt = extract_seniority_info(norm_title)

        # Allow existing score if already populated by LLM, else fallback to dictionary score
        if "seniority_score" in item and item["seniority_score"] is not None:
            final_score = int(item["seniority_score"])
        else:
            final_score = SENIORITY_SCORES.get(seniority, score)

        final_seniority = item.get("seniority") or seniority
        final_mgmt = item.get("management_level") or mgmt

        dept, func = infer_department_and_function(norm_title, raw_dept)
        final_dept = item.get("department") or dept
        final_func = item.get("function") or func

        attr_record = {
            "id": emp_id,
            "name": item.get("name"),
            "original_title": item.get("original_title") or raw_info.get("title", ""),
            "normalized_title": norm_title,
            "department": final_dept,
            "function": final_func,
            "seniority": final_seniority,
            "seniority_score": final_score,
            "management_level": final_mgmt,
        }

        enriched_attributes.append(attr_record)
        updated_normalized.append(attr_record)

    return {
        "employee_attributes": enriched_attributes,
        "normalized_employees": updated_normalized,
    }
