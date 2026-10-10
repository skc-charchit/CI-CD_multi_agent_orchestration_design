"""Use cases for invoking the Agentic AI workflow."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from backend.features.agentic_ai.compile_agent import agent
from backend.models import AgentQuery
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage
from sqlalchemy import func, select
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class AgentTurn:
    """Answer and turn metadata returned after the turn is persisted."""

    answer: str
    input_at: datetime
    output_at: datetime
    tools_used: list[dict[str, Any]]
    messages: list[AnyMessage]
    activity_messages: list[AnyMessage]
    record_id: int


def _text_content(content: object) -> str | None:
    """Extract text from either plain-text or block-based model output."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            block["text"]
            for block in content
            if isinstance(block, dict)
            and block.get("type") == "text"
            and isinstance(block.get("text"), str)
        ]
        return "\n".join(parts) if parts else None
    return None


def _tool_activity(messages: Sequence[AnyMessage]) -> list[dict[str, Any]]:
    """Collect each requested tool, its arguments, and its returned result."""
    results = {
        message.tool_call_id: message.content
        for message in messages
        if isinstance(message, ToolMessage)
    }
    activity: list[dict[str, Any]] = []
    for message in messages:
        if not isinstance(message, AIMessage):
            continue
        for call in message.tool_calls:
            call_id = call["id"]
            result = results.get(call_id) if call_id is not None else None
            result_text = _text_content(result)
            activity.append(
                {
                    "name": call["name"],
                    "arguments": call["args"],
                    "result": result_text if result_text is not None else result,
                }
            )
    return activity


def answer_message(
    message: str,
    session: Session,
    history: Sequence[AnyMessage] = (),
) -> AgentTurn:
    """Run one user turn and persist its input, answer, timestamps, and tools."""
    input_at = datetime.now(UTC)
    result = agent.invoke({"messages": [*history, HumanMessage(content=message)]})
    messages = result["messages"]
    turn_messages = messages[len(history) :]
    answer = next(
        (
            text
            for response in reversed(turn_messages)
            if isinstance(response, AIMessage) and not response.tool_calls
            if (text := _text_content(response.content))
        ),
        None,
    )
    if not answer:
        raise RuntimeError("The agent did not return a text response.")

    output_at = datetime.now(UTC)
    tools_used = _tool_activity(turn_messages)
    record = AgentQuery(
        question=message,
        answer=answer,
        input_at=input_at,
        output_at=output_at,
        tools_used=tools_used,
        query_date=input_at.date(),
    )
    try:
        session.add(record)
        session.flush()
        record_id = record.id
        assert record_id is not None
        session.commit()
    except Exception:
        session.rollback()
        raise

    return AgentTurn(
        answer=answer,
        input_at=input_at,
        output_at=output_at,
        tools_used=tools_used,
        messages=list(messages),
        activity_messages=list(turn_messages),
        record_id=record_id,
    )


def list_saved_turns(
    session: Session,
    *,
    limit: int,
    offset: int,
) -> tuple[list[AgentQuery], int]:
    """Return a newest-first page of saved turns and the total row count."""
    total = session.scalar(select(func.count()).select_from(AgentQuery)) or 0
    statement = (
        select(AgentQuery)
        .order_by(AgentQuery.input_at.desc(), AgentQuery.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(session.scalars(statement).all()), total
