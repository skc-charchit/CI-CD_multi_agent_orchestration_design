from backend.features.agentic_ai.state import AgentState
from backend.features.agentic_ai.tools import get_model_with_tools
from langchain_core.messages import SystemMessage


def llm_call(state: AgentState) -> dict[str, object]:
    """Ask the model to answer or select one of the bound arithmetic tools."""

    return {
        "messages": [
            get_model_with_tools().invoke(
                [
                    SystemMessage(
                        content=(
                            "You are a helpful assistant tasked with performing "
                            "arithmetic on a set of inputs."
                        )
                    )
                ]
                + state["messages"]
            )
        ],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }
