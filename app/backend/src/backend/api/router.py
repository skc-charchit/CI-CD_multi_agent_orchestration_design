"""Assemble versioned API routes from shared and feature-owned routers."""

from backend.api.routes.health import router as health_router
from backend.features.echo.api.routes import router as echo_router
from fastapi import APIRouter

API_V1_PREFIX = "/api/v1"
api_router = APIRouter(prefix=API_V1_PREFIX)
api_router.include_router(health_router)
api_router.include_router(echo_router)
