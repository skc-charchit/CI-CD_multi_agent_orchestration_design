"""Public request and response contracts for the echo feature."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EchoRequest(BaseModel):
    """Text submitted by a client to verify API connectivity."""

    message: str = Field(
        min_length=1,
        max_length=500,
        description="Message to echo back to the caller.",
        examples=["Hello from Feature Studio"],
    )


class EchoResponse(BaseModel):
    """Acknowledgement returned by the API."""

    id: UUID
    message: str
    received_at: datetime
