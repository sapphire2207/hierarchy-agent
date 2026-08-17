"""Hierarchy analysis API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.core.logging import logger
from backend.app.schemas.hierarchy import (
    FinalHierarchyResponse,
    HierarchyAnalyzeRequest,
)
from backend.app.services.hierarchy_service import (
    HierarchyService,
    get_hierarchy_service,
)

router = APIRouter(prefix="/hierarchy", tags=["Hierarchy Analysis"])


@router.post(
    "/analyze",
    response_model=FinalHierarchyResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze organizational hierarchy and classify buying roles",
    description="Takes a list of employees with job titles and optional departments, normalizes titles, extracts attributes, infers tree hierarchy, and classifies B2B buying roles.",
)
async def analyze_hierarchy(
    request: HierarchyAnalyzeRequest,
    service: HierarchyService = Depends(get_hierarchy_service),
) -> FinalHierarchyResponse:
    """
    Analyzes organizational hierarchy and classifies buying roles for a list of employees.
    """
    try:
        response = service.analyze(request)
        return response
    except ValueError as ve:
        logger.warning(f"Validation error in hierarchy analysis request: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        ) from ve
    except Exception as exc:
        logger.error(f"Unexpected error in hierarchy analysis: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the organizational hierarchy analysis.",
        ) from exc
