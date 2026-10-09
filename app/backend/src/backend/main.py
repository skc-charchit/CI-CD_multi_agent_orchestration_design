"""FastAPI application factory and top-level composition."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.router import API_V1_PREFIX, api_router
from backend.core.config import settings


def create_app() -> FastAPI:
    """Create the configured FastAPI application."""
    application = FastAPI(
        title="Feature Studio API",
        description=(
            "Feature Studio API. Each product feature owns its routes, "
            "schemas, and application services."
        ),
        version="0.1.0",
        debug=settings.debug,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    application.include_router(api_router)

    @application.get(
        "/",
        tags=["health"],
        summary="API overview",
        description="Returns links to the API documentation and health endpoint.",
    )
    def root() -> dict[str, str]:
        return {
            "message": f"Welcome to {settings.app_name}",
            "docs": "/docs",
            "health": f"{API_V1_PREFIX}/health",
        }

    return application


app = create_app()
