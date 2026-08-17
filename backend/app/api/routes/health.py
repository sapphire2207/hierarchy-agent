"""Health check API endpoints."""

from fastapi import APIRouter, status

router = APIRouter(tags=["System"])


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
    description="Returns the operational status of the backend API.",
)
async def health_check() -> dict[str, str]:
    """Health check endpoint to verify backend service availability."""
    return {"status": "ok"}
