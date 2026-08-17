"""LangGraph typed state definition for hierarchy and buying-role analysis."""

from typing import Any

from typing_extensions import TypedDict


class HierarchyState(TypedDict, total=False):
    """
    Serializable state passed across LangGraph nodes.
    """

    company: str | None
    employees: list[dict[str, Any]]
    normalized_employees: list[dict[str, Any]]
    employee_attributes: list[dict[str, Any]]
    hierarchy_relationships: list[dict[str, Any]]
    role_classifications: list[dict[str, Any]]
    validation_results: dict[str, Any]
    final_output: dict[str, Any] | None
    errors: list[str]
    retry_count: int
