"""HTTP routes for the echo example feature."""

from backend.features.echo.schemas import EchoRequest, EchoResponse
from backend.features.echo.service import echo_message
from fastapi import APIRouter

router = APIRouter(prefix="/examples", tags=["echo"])


@router.post(
    "/echo",
    response_model=EchoResponse,
    summary="Echo a message",
    description=(
        "Validate a short message and return it with a request ID and "
        "UTC timestamp. This demonstration endpoint does not persist data."
    ),
)
def post_echo(request: EchoRequest) -> EchoResponse:
    """Return a validated message with a request ID and server timestamp."""
    return echo_message(request)
