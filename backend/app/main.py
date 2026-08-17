"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.routes.hierarchy import router as hierarchy_router
from backend.app.core.config import get_settings
from backend.app.core.logging import logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifespan events."""
    settings = get_settings()
    setup_logging(settings.log_level)
    logger.info(
        f"Starting {settings.app_name} in {settings.app_env} mode (LLM Provider: {settings.llm_provider})"
    )
    yield
    logger.info("Shutting down application...")


def create_application() -> FastAPI:
    """Creates and configures the FastAPI application instance."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Production backend MVP for organizational hierarchy inference and B2B buying-role classification.",
        lifespan=lifespan,
    )

    # Enable CORS for frontend consumption
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API routers
    app.include_router(hierarchy_router, prefix="/api/v1")

    # Health Check Endpoint
    @app.get(
        "/health",
        status_code=status.HTTP_200_OK,
        tags=["System"],
        summary="Health check endpoint",
    )
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    # Global Exception Handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred."},
        )

    return app


app = create_application()
