"""FastAPI application factory and top-level composition."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from backend.api.router import API_V1_PREFIX, api_router
from backend.core.config import settings
from backend.db.engine import check_database_connection
from backend.db.schema import create_schema
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Check configured infrastructure before serving requests."""
    check_database_connection()
    create_schema()
    yield


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
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
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
