"""Tests for the Agentic AI HTTP contract."""

from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from backend.core.config import Settings
from backend.db.base import Base
from backend.features.agentic_ai import service
from backend.features.agentic_ai.api import routes
from backend.features.agentic_ai.tools import ModelConfigurationError
from backend.main import app
from backend.models import AgentQuery
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from pydantic import SecretStr
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

client = TestClient(app)
AUTH_HEADERS = {"Authorization": "Bearer test-agent-key"}


def configure_test_api_key(monkeypatch) -> None:
    monkeypatch.setattr(
        routes,
        "get_settings",
        lambda: Settings.model_construct(
            agent_api_key=SecretStr("test-agent-key"),
        ),
    )


@pytest.fixture
def db_session(monkeypatch) -> Generator[Session, None, None]:
    """Provide isolated persistence for chat endpoint tests."""
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        monkeypatch.setitem(
            app.dependency_overrides,
            routes.get_agent_session,
            lambda: session,
        )
        yield session
    test_engine.dispose()


def test_chat_endpoint_returns_agent_answer(monkeypatch, db_session: Session) -> None:
    configure_test_api_key(monkeypatch)

    def fake_invoke(inputs):
        return {
            "messages": [
                *inputs["messages"],
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "add",
                            "args": {"a": 19, "b": 23},
                            "id": "call-1",
                            "type": "tool_call",
                        }
                    ],
                ),
                ToolMessage(content="42", tool_call_id="call-1"),
                AIMessage(content="The answer is 42."),
            ]
        }

    monkeypatch.setattr(service.agent, "invoke", fake_invoke)

    response = client.post(
        "/api/v1/agentic-ai/chat",
        json={"message": "What is 19 + 23?"},
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200
    assert response.json() == {"answer": "The answer is 42."}
    saved = db_session.query(AgentQuery).one()
    assert saved.question == "What is 19 + 23?"
    assert saved.answer == "The answer is 42."
    assert saved.input_at is not None
    assert saved.output_at is not None
    assert saved.input_at.replace(tzinfo=UTC) <= saved.output_at.replace(tzinfo=UTC)
    assert saved.tools_used == [
        {
            "name": "add",
            "arguments": {"a": 19, "b": 23},
            "result": "42",
        }
    ]


def test_each_continued_chat_turn_is_persisted(
    monkeypatch,
    db_session: Session,
) -> None:
    calls = 0

    def fake_invoke(inputs):
        nonlocal calls
        calls += 1
        messages = inputs["messages"]
        if calls == 1:
            return {
                "messages": [
                    *messages,
                    AIMessage(
                        content="",
                        tool_calls=[
                            {
                                "name": "multiply",
                                "args": {"a": 6, "b": 7},
                                "id": "call-1",
                                "type": "tool_call",
                            }
                        ],
                    ),
                    ToolMessage(content="42", tool_call_id="call-1"),
                    AIMessage(content="It is 42."),
                ]
            }
        assert isinstance(messages[-1], HumanMessage)
        assert messages[-1].content == "Is that correct?"
        return {"messages": [*messages, AIMessage(content="Yes, 42 is correct.")]}

    monkeypatch.setattr(service.agent, "invoke", fake_invoke)

    first_turn = service.answer_message("What is 6 times 7?", db_session)
    second_turn = service.answer_message(
        "Is that correct?",
        db_session,
        first_turn.messages,
    )

    with Session(db_session.get_bind()) as persisted_session:
        saved_turns = persisted_session.query(AgentQuery).order_by(AgentQuery.id).all()
    assert len(saved_turns) == 2
    assert [turn.question for turn in saved_turns] == [
        "What is 6 times 7?",
        "Is that correct?",
    ]
    assert [turn.answer for turn in saved_turns] == [
        "It is 42.",
        "Yes, 42 is correct.",
    ]
    assert all(turn.input_at is not None for turn in saved_turns)
    assert all(turn.output_at is not None for turn in saved_turns)
    assert all(
        turn.input_at.replace(tzinfo=UTC) <= turn.output_at.replace(tzinfo=UTC)
        for turn in saved_turns
    )
    assert saved_turns[0].tools_used == [
        {
            "name": "multiply",
            "arguments": {"a": 6, "b": 7},
            "result": "42",
        }
    ]
    assert saved_turns[1].tools_used == []
    assert second_turn.messages[-1].content == "Yes, 42 is correct."


def test_history_endpoint_lists_saved_turns_with_pagination(
    monkeypatch,
    db_session: Session,
) -> None:
    configure_test_api_key(monkeypatch)
    first_input = datetime(2026, 10, 10, 12, 0, tzinfo=UTC)
    db_session.add_all(
        [
            AgentQuery(
                question="What is 6 times 7?",
                answer="42",
                input_at=first_input,
                output_at=first_input + timedelta(seconds=1),
                tools_used=[
                    {
                        "name": "multiply",
                        "arguments": {"a": 6, "b": 7},
                        "result": "42",
                    }
                ],
                query_date=first_input.date(),
            ),
            AgentQuery(
                question="Is that correct?",
                answer="Yes.",
                input_at=first_input + timedelta(minutes=1),
                output_at=first_input + timedelta(minutes=1, seconds=1),
                tools_used=[],
                query_date=first_input.date(),
            ),
        ]
    )
    db_session.commit()

    response = client.get(
        "/api/v1/agentic-ai/history?limit=1&offset=0",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": 2,
                "question": "Is that correct?",
                "answer": "Yes.",
                "input_at": "2026-10-10T12:01:00",
                "output_at": "2026-10-10T12:01:01",
                "tools_used": [],
            }
        ],
        "total": 2,
        "limit": 1,
        "offset": 0,
    }

    next_page = client.get(
        "/api/v1/agentic-ai/history?limit=1&offset=1",
        headers=AUTH_HEADERS,
    )
    assert next_page.status_code == 200
    assert next_page.json()["items"][0]["tools_used"] == [
        {
            "name": "multiply",
            "arguments": {"a": 6, "b": 7},
            "result": "42",
        }
    ]


def test_history_endpoint_requires_authentication(monkeypatch) -> None:
    configure_test_api_key(monkeypatch)
    response = client.get("/api/v1/agentic-ai/history")

    assert response.status_code == 401


def test_chat_endpoint_rejects_empty_message(
    monkeypatch,
    db_session: Session,
) -> None:
    configure_test_api_key(monkeypatch)
    assert db_session.is_active
    response = client.post(
        "/api/v1/agentic-ai/chat",
        json={"message": ""},
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 422


def test_chat_endpoint_rejects_missing_authentication(monkeypatch) -> None:
    configure_test_api_key(monkeypatch)
    response = client.post(
        "/api/v1/agentic-ai/chat",
        json={"message": "What is 19 + 23?"},
    )

    assert response.status_code == 401


def test_chat_endpoint_reports_unconfigured_authentication(monkeypatch) -> None:
    monkeypatch.setattr(
        routes,
        "get_settings",
        lambda: Settings.model_construct(agent_api_key=None),
    )
    response = client.post(
        "/api/v1/agentic-ai/chat",
        json={"message": "What is 19 + 23?"},
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Agent API authentication is not configured."}


def test_chat_endpoint_reports_unconfigured_database(monkeypatch) -> None:
    configure_test_api_key(monkeypatch)
    monkeypatch.setattr(routes, "SessionLocal", None)

    response = client.post(
        "/api/v1/agentic-ai/chat",
        json={"message": "What is 19 + 23?"},
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 503
    assert "Database is not configured" in response.json()["detail"]


def test_chat_endpoint_reports_missing_provider_credentials(
    monkeypatch,
    db_session: Session,
) -> None:
    configure_test_api_key(monkeypatch)
    assert db_session.is_active

    def raise_missing_credentials(message: str, session: Session) -> str:
        assert message
        assert session.is_active
        raise ModelConfigurationError("OPENAI_API_KEY is not set.")

    monkeypatch.setattr(routes, "answer_message", raise_missing_credentials)

    response = client.post(
        "/api/v1/agentic-ai/chat",
        json={"message": "What is 19 + 23?"},
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "OPENAI_API_KEY is not set."}


def test_chat_endpoint_allows_authenticated_browser_preflight() -> None:
    response = client.options(
        "/api/v1/agentic-ai/chat",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "authorization" in response.headers["access-control-allow-headers"].lower()
