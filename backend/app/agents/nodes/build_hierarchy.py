"""Node for inferring organizational hierarchy relationships."""

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from backend.app.agents.prompts.hierarchy import (
    HIERARCHY_SYSTEM_PROMPT,
    HIERARCHY_USER_PROMPT,
)
from backend.app.agents.prompts.validation import (
    HIERARCHY_REPAIR_SYSTEM_PROMPT,
    HIERARCHY_REPAIR_USER_PROMPT,
)
from backend.app.agents.state import HierarchyState
from backend.app.core.logging import logger
from backend.app.schemas.hierarchy import BatchHierarchyInference
from backend.app.services.llm_service import get_llm_service


def build_hierarchy_node(state: HierarchyState) -> dict[str, Any]:
    """
    Infers organizational hierarchy relationships across the entire employee list holistically.
    """
    logger.info("Executing build_hierarchy node")
    normalized_employees = state.get("normalized_employees", [])
    company = state.get("company", "Company")
    errors = state.get("errors", [])
    retry_count = state.get("retry_count", 0)

    if not normalized_employees:
        return {"hierarchy_relationships": []}

    llm_service = get_llm_service()
    structured_llm = llm_service.get_structured_llm(BatchHierarchyInference)

    payload_str = json.dumps(normalized_employees, indent=2)

    # Use repair prompt if this is a validation retry
    if retry_count > 0 and errors:
        system_prompt = HIERARCHY_REPAIR_SYSTEM_PROMPT
        user_prompt = HIERARCHY_REPAIR_USER_PROMPT.format(
            company=company,
            validation_errors="\n".join(f"- {e}" for e in errors),
            normalized_employees_payload=payload_str,
        )
    else:
        system_prompt = HIERARCHY_SYSTEM_PROMPT
        user_prompt = HIERARCHY_USER_PROMPT.format(
            company=company,
            normalized_employees_payload=payload_str,
        )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    try:
        response: BatchHierarchyInference = structured_llm.invoke(messages)
        relationships = [r.model_dump() for r in response.relationships]
    except Exception as exc:
        logger.error(f"Error during hierarchy inference: {exc}")
        # Fallback to mock LLM inference for safety
        from backend.app.services.llm_service import MockStructuredLLM

        mock_llm = MockStructuredLLM(schema=BatchHierarchyInference)
        response = mock_llm.invoke(messages)
        relationships = [r.model_dump() for r in response.relationships]

    return {"hierarchy_relationships": relationships}
