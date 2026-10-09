"""Health check route used by local tooling and deployment probes."""

from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/health",
    tags=["health"],
    summary="Health check",
    description="Confirms that the API process is responding.",
)
def health_check() -> dict[str, str]:
    return {"status": "ok"}
