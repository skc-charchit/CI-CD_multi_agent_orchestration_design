"""Tests for the Agentic AI graph components that do not call a model."""

from unittest.mock import Mock

import pytest
from backend.features.agentic_ai.compile_agent import agent
from backend.features.agentic_ai.end_logic import should_continue
from backend.features.agentic_ai.state import AgentState
from backend.features.agentic_ai.tool_node import tool_node
from backend.features.agentic_ai.tools import (
    add,
    divide,
    get_model_with_tools,
    multiply,
)
from langchain_core.messages import AIMessage, ToolMessage


def test_graph_compiles() -> None:
    assert agent is not None


def test_model_factory_uses_google_api_key_from_environment(monkeypatch) -> None:
    fake_model = Mock()
    fake_model.bind_tools.return_value = "model with tools"
    init_chat_model = Mock(return_value=fake_model)
    monkeypatch.setattr(
        "backend.features.agentic_ai.tools.init_chat_model",
        init_chat_model,
    )
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    get_model_with_tools.cache_clear()

    try:
        assert get_model_with_tools() == "model with tools"
    finally:
        get_model_with_tools.cache_clear()

    init_chat_model.assert_called_once_with(
        "gemini-3.8-flash",
        model_provider="google_genai",
        temperature=0,
        api_key="test-key",
    )


def test_model_factory_reports_missing_google_api_key(monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    get_model_with_tools.cache_clear()

    try:
        with pytest.raises(RuntimeError, match="GOOGLE_API_KEY is not set"):
            get_model_with_tools()
    finally:
        get_model_with_tools.cache_clear()


@pytest.mark.parametrize(
    ("tool", "arguments", "expected"),
    [
        (add, {"a": 3, "b": 4}, 7),
        (multiply, {"a": 3, "b": 4}, 12),
        (divide, {"a": 8, "b": 2}, 4.0),
    ],
)
def test_arithmetic_tools(
    tool, arguments: dict[str, int], expected: int | float
) -> None:
    assert tool.invoke(arguments) == expected


def test_divide_rejects_zero_divisor() -> None:
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide.invoke({"a": 1, "b": 0})


def test_should_continue_routes_tool_calls() -> None:
    state: AgentState = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "add",
                        "args": {"a": 3, "b": 4},
                        "id": "call-1",
                        "type": "tool_call",
                    }
                ],
            )
        ]
    }

    assert should_continue(state) == "tool_node"


def test_should_continue_finishes_without_tool_calls() -> None:
    state: AgentState = {"messages": [AIMessage(content="The answer is 7.")]}

    assert should_continue(state) == "__end__"


def test_should_continue_finishes_for_non_model_message() -> None:
    state: AgentState = {"messages": [ToolMessage(content="7", tool_call_id="call-1")]}

    assert should_continue(state) == "__end__"


def test_tool_node_returns_tool_message() -> None:
    state: AgentState = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "add",
                        "args": {"a": 3, "b": 4},
                        "id": "call-1",
                        "type": "tool_call",
                    }
                ],
            )
        ]
    }

    result = tool_node(state)

    assert result["messages"] == [ToolMessage(content="7", tool_call_id="call-1")]
