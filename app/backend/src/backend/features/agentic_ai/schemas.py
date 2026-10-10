"""Public request and response contracts for the agent feature."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentChatRequest(BaseModel):
    """A single message submitted to the arithmetic agent."""

    message: str = Field(
        min_length=1,
        max_length=2_000,
        description="Question or instruction for the arithmetic assistant.",
    )


class AgentChatResponse(BaseModel):
    """The agent's final user-facing answer."""

    answer: str


class AgentToolUsage(BaseModel):
    """A tool invoked while producing an agent answer."""

    name: str
    arguments: dict[str, Any]
    result: Any = None


class AgentQueryResponse(BaseModel):
    """One persisted question, answer, timestamp pair, and tool activity."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    answer: str
    input_at: datetime
    output_at: datetime
    tools_used: list[AgentToolUsage]


class AgentHistoryResponse(BaseModel):
    """A page of persisted agent turns."""

    items: list[AgentQueryResponse]
    total: int
    limit: int
    offset: int
