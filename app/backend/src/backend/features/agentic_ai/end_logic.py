from typing import Literal

from backend.features.agentic_ai.state import AgentState
from langchain_core.messages import AIMessage


def should_continue(state: AgentState) -> Literal["tool_node", "__end__"]:
    """Route to tools when the latest model message requests a tool call."""

    messages = state["messages"]
    if not messages:
        return "__end__"

    last_message = messages[-1]

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tool_node"

    return "__end__"
