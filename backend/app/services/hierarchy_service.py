"""Service layer orchestrating hierarchy analysis and LangGraph workflow."""

import time

from backend.app.agents.graph import build_hierarchy_graph
from backend.app.agents.state import HierarchyState
from backend.app.core.logging import logger
from backend.app.schemas.hierarchy import (
    AnalysisMetadata,
    FinalHierarchyResponse,
    HierarchyAnalyzeRequest,
)


class HierarchyService:
    """Service encapsulating the LangGraph hierarchy and buying-role analysis workflow."""

    def __init__(self):
        self._graph = build_hierarchy_graph()

    def analyze(self, request: HierarchyAnalyzeRequest) -> FinalHierarchyResponse:
        """
        Executes the LangGraph analysis pipeline for the given employee hierarchy request.
        """
        start_time = time.perf_counter()
        emp_count = len(request.employees)
        logger.info(
            f"Initiating hierarchy analysis for company '{request.company}' with {emp_count} employee(s)."
        )

        initial_state: HierarchyState = {
            "company": request.company,
            "employees": [emp.model_dump() for emp in request.employees],
            "normalized_employees": [],
            "employee_attributes": [],
            "hierarchy_relationships": [],
            "role_classifications": [],
            "validation_results": {},
            "final_output": None,
            "errors": [],
            "retry_count": 0,
        }

        try:
            final_state = self._graph.invoke(initial_state)
            execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

            raw_output = final_state.get("final_output")
            if raw_output:
                response = FinalHierarchyResponse.model_validate(raw_output)
                response.analysis_metadata.execution_time_ms = execution_time_ms
                logger.info(
                    f"Successfully completed analysis for '{request.company}' in {execution_time_ms}ms (roots: {response.analysis_metadata.root_count}, valid: {response.analysis_metadata.is_valid})."
                )
                return response
            else:
                # Handle unexpected missing output
                logger.error("LangGraph completed without producing final_output.")
                return FinalHierarchyResponse(
                    company=request.company,
                    people=[],
                    root_employee_ids=[],
                    analysis_metadata=AnalysisMetadata(
                        total_employees=0,
                        root_count=0,
                        execution_time_ms=execution_time_ms,
                        is_valid=False,
                        warnings=["Workflow finished without final output."],
                    ),
                )

        except Exception as exc:
            execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"Error during hierarchy graph execution for '{request.company}': {exc}",
                exc_info=True,
            )
            raise


_hierarchy_service_instance: HierarchyService | None = None


def get_hierarchy_service() -> HierarchyService:
    """Returns singleton instance of HierarchyService."""
    global _hierarchy_service_instance
    if _hierarchy_service_instance is None:
        _hierarchy_service_instance = HierarchyService()
    return _hierarchy_service_instance
