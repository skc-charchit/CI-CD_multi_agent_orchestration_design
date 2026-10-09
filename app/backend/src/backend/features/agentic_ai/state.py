from typing import NotRequired

from langgraph.graph import MessagesState


class AgentState(MessagesState):
    """State shared between chatbot graph nodes."""

    llm_calls: NotRequired[int]
