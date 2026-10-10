"""Health-check endpoint for the API."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health check")
def health_check() -> dict[str, str]:
    """Confirms that the API process is responding."""
    return {"status": "ok"}
