"""Node for classifying B2B buying roles."""

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from backend.app.agents.prompts.roles import (
    ROLES_SYSTEM_PROMPT,
    ROLES_USER_PROMPT,
)
from backend.app.agents.state import HierarchyState
from backend.app.core.logging import logger
from backend.app.schemas.classification import BatchRoleClassification
from backend.app.services.llm_service import get_llm_service


def classify_roles_node(state: HierarchyState) -> dict[str, Any]:
    """
    Classifies buying roles for all employees based on normalized titles, hierarchy position,
    and departmental scope.
    """
    logger.info("Executing classify_roles node")
    normalized_employees = state.get("normalized_employees", [])
    relationships = state.get("hierarchy_relationships", [])
    company = state.get("company", "Company")

    if not normalized_employees:
        return {"role_classifications": []}

    # Map reports_to for prompt context
    parent_map = {str(r.get("employee_id")): r.get("parent_id") for r in relationships}

    employees_for_prompt: list[dict[str, Any]] = []
    for emp in normalized_employees:
        emp_id = str(emp.get("id"))
        record = dict(emp)
        record["reports_to"] = parent_map.get(emp_id)
        employees_for_prompt.append(record)

    llm_service = get_llm_service()
    structured_llm = llm_service.get_structured_llm(BatchRoleClassification)

    payload_str = json.dumps(employees_for_prompt, indent=2)
    messages = [
        SystemMessage(content=ROLES_SYSTEM_PROMPT),
        HumanMessage(
            content=ROLES_USER_PROMPT.format(
                company=company,
                employees_with_hierarchy_payload=payload_str,
            )
        ),
    ]

    try:
        response: BatchRoleClassification = structured_llm.invoke(messages)
        roles = [r.model_dump() for r in response.roles]
    except Exception as exc:
        logger.error(f"Error during role classification: {exc}")
        from backend.app.services.llm_service import MockStructuredLLM

        mock_llm = MockStructuredLLM(schema=BatchRoleClassification)
        response = mock_llm.invoke(messages)
        roles = [r.model_dump() for r in response.roles]

    return {"role_classifications": roles}
