"""Construct the LangGraph arithmetic agent."""

from backend.features.agentic_ai.end_logic import should_continue
from backend.features.agentic_ai.model_node import llm_call
from backend.features.agentic_ai.state import AgentState
from backend.features.agentic_ai.tool_node import tool_node
from langgraph.graph import END, START, StateGraph


def build_agent():
    """Build and compile the chatbot graph."""
    agent_builder = StateGraph(AgentState)
    agent_builder.add_node("llm_call", llm_call)
    agent_builder.add_node("tool_node", tool_node)

    agent_builder.add_edge(START, "llm_call")
    agent_builder.add_conditional_edges(
        "llm_call",
        should_continue,
        ["tool_node", END],
    )
    agent_builder.add_edge("tool_node", "llm_call")

    return agent_builder.compile()


agent = build_agent()
