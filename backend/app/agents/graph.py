"""LangGraph workflow assembly for hierarchy and buying-role classification."""

from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from backend.app.agents.nodes.build_hierarchy import build_hierarchy_node
from backend.app.agents.nodes.classify_roles import classify_roles_node
from backend.app.agents.nodes.extract_attributes import extract_attributes_node
from backend.app.agents.nodes.normalize import normalize_titles_node
from backend.app.agents.nodes.validate import (
    validate_input_node,
    validate_results_node,
)
from backend.app.agents.state import HierarchyState
from backend.app.core.config import get_settings
from backend.app.core.logging import logger
from backend.app.schemas.classification import BuyingRole
from backend.app.schemas.employee import FinalEmployeeAnalysis
from backend.app.schemas.hierarchy import AnalysisMetadata, FinalHierarchyResponse


def compile_final_output_node(state: HierarchyState) -> dict[str, Any]:
    """
    Compiles the final structured response from validated state.
    """
    logger.info("Executing compile_final_output node")
    company = state.get("company", "Unknown Company")
    normalized_employees = state.get("normalized_employees", [])
    relationships = state.get("hierarchy_relationships", [])
    roles = state.get("role_classifications", [])
    validation_results = state.get("validation_results", {})
    retry_count = state.get("retry_count", 0)

    # Index relationships and roles by employee_id
    rel_map = {str(r.get("employee_id")): r for r in relationships}
    role_map = {str(r.get("employee_id")): r for r in roles}

    people: list[FinalEmployeeAnalysis] = []
    root_ids: list[str] = []

    for emp in normalized_employees:
        emp_id = str(emp.get("id"))
        rel = rel_map.get(emp_id, {})
        role = role_map.get(emp_id, {})

        parent_id = rel.get("parent_id")
        if parent_id is None:
            root_ids.append(emp_id)

        raw_role = role.get("buying_role", BuyingRole.UNKNOWN.value)
        role_enum_val = raw_role.value if hasattr(raw_role, "value") else str(raw_role)
        try:
            buying_role = BuyingRole(role_enum_val)
        except ValueError:
            buying_role = BuyingRole.UNKNOWN

        people.append(
            FinalEmployeeAnalysis(
                id=emp_id,
                name=emp.get("name"),
                original_title=emp.get("original_title", ""),
                normalized_title=emp.get("normalized_title", ""),
                department=emp.get("department"),
                function=emp.get("function"),
                seniority=emp.get("seniority", "Unknown"),
                seniority_score=emp.get("seniority_score", 0),
                management_level=emp.get("management_level", "Individual Contributor"),
                reports_to=parent_id,
                buying_role=buying_role,
                confidence=float(role.get("confidence", 0.5)),
                reason=role.get(
                    "reason", "Inferred role based on title and organizational position."
                ),
                supporting_factors=role.get("supporting_factors", []),
            )
        )

    # Calculate metadata
    metadata = AnalysisMetadata(
        total_employees=len(people),
        root_count=len(root_ids),
        retry_count=retry_count,
        is_valid=validation_results.get("is_valid", True),
        warnings=validation_results.get("warnings", []),
    )

    response = FinalHierarchyResponse(
        company=company,
        people=people,
        root_employee_ids=root_ids,
        analysis_metadata=metadata,
    )

    return {"final_output": response.model_dump()}


def route_after_input_validation(
    state: HierarchyState,
) -> Literal["normalize_titles", "compile_final_output"]:
    """Conditional router: If input validation failed with errors, jump straight to output."""
    validation = state.get("validation_results", {})
    if not validation.get("is_valid", True):
        logger.warning(
            f"Input validation failed: {validation.get('errors')}. Skipping downstream steps."
        )
        return "compile_final_output"
    return "normalize_titles"


def route_after_validation(
    state: HierarchyState,
) -> Literal["build_hierarchy", "compile_final_output"]:
    """
    Conditional router: If validation failed and retries remain, retry hierarchy inference.
    Otherwise proceed to compile output.
    """
    settings = get_settings()
    validation = state.get("validation_results", {})
    is_valid = validation.get("is_valid", True)
    retry_count = state.get("retry_count", 0)

    if not is_valid and retry_count <= settings.max_retries:
        logger.warning(
            f"Hierarchy validation failed with {len(validation.get('errors', []))} error(s). Retrying inference (attempt {retry_count}/{settings.max_retries})."
        )
        return "build_hierarchy"

    return "compile_final_output"


def build_hierarchy_graph():
    """Assembles and compiles the LangGraph StateGraph workflow."""
    workflow = StateGraph(HierarchyState)

    # Register Nodes
    workflow.add_node("validate_input", validate_input_node)
    workflow.add_node("normalize_titles", normalize_titles_node)
    workflow.add_node("extract_attributes", extract_attributes_node)
    workflow.add_node("build_hierarchy", build_hierarchy_node)
    workflow.add_node("classify_roles", classify_roles_node)
    workflow.add_node("validate_results", validate_results_node)
    workflow.add_node("compile_final_output", compile_final_output_node)

    # Edge Definitions
    workflow.add_edge(START, "validate_input")

    workflow.add_conditional_edges(
        "validate_input",
        route_after_input_validation,
        {
            "normalize_titles": "normalize_titles",
            "compile_final_output": "compile_final_output",
        },
    )

    workflow.add_edge("normalize_titles", "extract_attributes")
    workflow.add_edge("extract_attributes", "build_hierarchy")
    workflow.add_edge("build_hierarchy", "classify_roles")
    workflow.add_edge("classify_roles", "validate_results")

    workflow.add_conditional_edges(
        "validate_results",
        route_after_validation,
        {
            "build_hierarchy": "build_hierarchy",
            "compile_final_output": "compile_final_output",
        },
    )

    workflow.add_edge("compile_final_output", END)

    return workflow.compile()
