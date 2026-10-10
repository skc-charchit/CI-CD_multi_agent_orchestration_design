from backend.features.agentic_ai.state import AgentState
from backend.features.agentic_ai.tools import tools_by_name
from langchain_core.messages import AIMessage, ToolMessage


def tool_node(state: AgentState) -> dict[str, list[ToolMessage]]:
    """Execute the tools requested by the latest model message."""

    messages = state["messages"]
    if not messages or not isinstance(messages[-1], AIMessage):
        raise ValueError("Tool node requires a model message with tool calls.")

    result = []
    for tool_call in messages[-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(
            ToolMessage(content=str(observation), tool_call_id=tool_call["id"])
        )
    return {"messages": result}
