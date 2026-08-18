"""FastAPI application entry point."""

from fastapi import FastAPI

from src.backend.api.v1.health import router as health_router
from src.backend.config import settings

app = FastAPI(title=settings.app_name, debug=settings.debug)
app.include_router(health_router, prefix=settings.api_v1_prefix)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": f"Welcome to {settings.app_name}"}
