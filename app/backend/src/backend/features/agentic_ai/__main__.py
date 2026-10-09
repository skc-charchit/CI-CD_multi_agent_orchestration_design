"""Run the Agentic AI arithmetic agent in an interactive terminal session."""

from collections.abc import Sequence

from backend.features.agentic_ai.compile_agent import agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage


def _content_text(content: object) -> str:
    """Extract user-readable text from supported LangChain message content."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            str(block["text"])
            for block in content
            if isinstance(block, dict)
            and block.get("type") == "text"
            and "text" in block
        )
    return ""


def _print_tool_activity(messages: Sequence[object]) -> None:
    """Show tool calls and results from the current graph turn."""
    call_names: dict[str, str] = {}
    for message in messages:
        if isinstance(message, AIMessage):
            for call in message.tool_calls:
                call_names[call["id"]] = call["name"]
                print(f"  Tool: {call['name']}({call['args']})")
        elif isinstance(message, ToolMessage):
            name = call_names.get(message.tool_call_id, "tool")
            print(f"  {name} result: {_content_text(message.content)}")


def run_cli() -> None:
    """Prompt for user input and display each agent response."""
    print("Agentic AI arithmetic assistant")
    print("Enter a question, /reset to clear conversation, or /quit to exit.")

    history: list[HumanMessage | AIMessage | ToolMessage] = []
    while True:
        try:
            prompt = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return

        if not prompt:
            continue
        if prompt.lower() in {"/quit", "quit", "exit"}:
            print("Goodbye.")
            return
        if prompt.lower() == "/reset":
            history.clear()
            print("Conversation cleared.")
            continue

        previous_history = history
        try:
            result = agent.invoke(
                {"messages": [*previous_history, HumanMessage(content=prompt)]}
            )
        except Exception as error:
            print(f"Agent error ({type(error).__name__}): {error}")
            continue

        history = result["messages"]
        turn_messages = history[len(previous_history) :]
        _print_tool_activity(turn_messages)

        response = next(
            (
                message
                for message in reversed(turn_messages)
                if isinstance(message, AIMessage) and not message.tool_calls
            ),
            None,
        )
        answer = _content_text(response.content) if response else ""
        print(f"Agent: {answer or '[No text response returned]'}")


if __name__ == "__main__":
    run_cli()
