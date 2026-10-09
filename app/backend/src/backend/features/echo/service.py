"""Application logic for the echo feature."""

from datetime import UTC, datetime
from uuid import uuid4

from backend.features.echo.schemas import EchoRequest, EchoResponse


def echo_message(request: EchoRequest) -> EchoResponse:
    """Acknowledge a message without storing it or calling an AI provider."""
    return EchoResponse(
        id=uuid4(),
        message=request.message,
        received_at=datetime.now(UTC),
    )
