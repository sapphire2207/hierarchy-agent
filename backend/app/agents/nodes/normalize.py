"""Node for title normalization."""

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from backend.app.agents.prompts.normalization import (
    NORMALIZATION_SYSTEM_PROMPT,
    NORMALIZATION_USER_PROMPT,
)
from backend.app.agents.state import HierarchyState
from backend.app.core.logging import logger
from backend.app.schemas.employee import BatchTitleNormalization, NormalizedEmployee
from backend.app.services.llm_service import get_llm_service
from backend.app.utils.title_utils import (
    extract_seniority_info,
    infer_department_and_function,
    normalize_title_deterministic,
)


def normalize_titles_node(state: HierarchyState) -> dict[str, Any]:
    """
    Normalizes employee job titles using deterministic rules and LLM structured output.
    """
    logger.info("Executing normalize_titles node")
    employees = state.get("employees", [])
    company = state.get("company", "Company")

    if not employees:
        return {"normalized_employees": []}

    # Step 1: Pre-process with deterministic rules
    deterministic_normalized: list[NormalizedEmployee] = []
    for emp in employees:
        emp_id = str(emp.get("id"))
        raw_title = emp.get("title", "")
        raw_name = emp.get("name")
        raw_dept = emp.get("department")

        norm_title = normalize_title_deterministic(raw_title)
        seniority, score, mgmt = extract_seniority_info(norm_title)
        dept, func = infer_department_and_function(norm_title, raw_dept)

        deterministic_normalized.append(
            NormalizedEmployee(
                id=emp_id,
                name=raw_name,
                original_title=raw_title,
                normalized_title=norm_title,
                department=dept,
                function=func,
                seniority=seniority,
                seniority_score=score,
                management_level=mgmt,
            )
        )

    # Step 2: Use LLM structured output if live provider is configured
    llm_service = get_llm_service()
    if llm_service.settings.llm_provider != "mock" and llm_service.settings.llm_api_key:
        try:
            structured_llm = llm_service.get_structured_llm(BatchTitleNormalization)
            payload_str = json.dumps(
                [
                    {
                        "id": emp.get("id"),
                        "name": emp.get("name"),
                        "title": emp.get("title"),
                        "department": emp.get("department"),
                    }
                    for emp in employees
                ],
                indent=2,
            )
            messages = [
                SystemMessage(content=NORMALIZATION_SYSTEM_PROMPT),
                HumanMessage(
                    content=NORMALIZATION_USER_PROMPT.format(
                        company=company,
                        employee_payload=payload_str,
                    )
                ),
            ]
            response: BatchTitleNormalization = structured_llm.invoke(messages)
            if response and response.normalized_employees:
                normalized_data = [item.model_dump() for item in response.normalized_employees]
                return {"normalized_employees": normalized_data}
        except Exception as exc:
            logger.warning(
                f"LLM normalization call encountered error: {exc}. Using deterministic normalization."
            )

    return {"normalized_employees": [item.model_dump() for item in deterministic_normalized]}
