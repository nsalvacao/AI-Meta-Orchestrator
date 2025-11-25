"""FastAPI application for the AI Meta Orchestrator REST API.

This module provides the main FastAPI application with all routes configured.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_meta_orchestrator import __version__
from ai_meta_orchestrator.api.routes import (
    agents_router,
    health_router,
    plugins_router,
    templates_router,
    workflows_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Handle application startup and shutdown."""
    # Startup
    yield
    # Shutdown
    pass


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title="AI Meta Orchestrator API",
        description=(
            "REST API for the AI Meta Orchestrator. "
            "Provides endpoints for managing agents, workflows, templates, and plugins."
        ),
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health_router)
    app.include_router(agents_router)
    app.include_router(workflows_router)
    app.include_router(templates_router)
    app.include_router(plugins_router)

    # Root endpoint
    @app.get("/", tags=["Root"])
    def root() -> dict[str, str]:
        """Root endpoint with API information."""
        return {
            "name": "AI Meta Orchestrator API",
            "version": __version__,
            "docs": "/docs",
            "health": "/health",
        }

    return app


# Create the application instance
app = create_app()


def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    log_level: str = "info",
) -> None:
    """Run the API server.

    Args:
        host: Host to bind to.
        port: Port to listen on.
        reload: Enable auto-reload for development.
        log_level: Logging level.
    """
    import uvicorn

    uvicorn.run(
        "ai_meta_orchestrator.api.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
    )
