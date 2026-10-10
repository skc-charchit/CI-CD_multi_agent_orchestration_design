"""Run the Agentic AI arithmetic agent in an interactive terminal session."""

from collections.abc import Sequence

from backend.db.schema import create_schema
from backend.db.session import SessionLocal
from backend.features.agentic_ai.service import AgentTurn, answer_message
from langchain_core.messages import AIMessage, AnyMessage, ToolMessage
from sqlalchemy.exc import SQLAlchemyError


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
                call_id = call["id"]
                if call_id is not None:
                    call_names[call_id] = call["name"]
                print(f"  Tool: {call['name']}({call['args']})")
        elif isinstance(message, ToolMessage):
            name = call_names.get(message.tool_call_id, "tool")
            print(f"  {name} result: {_content_text(message.content)}")


def run_cli() -> None:
    """Prompt for user input and display each agent response."""
    print("Agentic AI arithmetic assistant")
    print("Enter a question, /reset to clear conversation, or /quit to exit.")

    try:
        create_schema(required=True)
    except (RuntimeError, SQLAlchemyError) as error:
        print(
            f"Database setup failed ({type(error).__name__}). "
            "Check PostgreSQL configuration and connectivity."
        )
        return

    if SessionLocal is None:
        print("Database is not configured; agent turns cannot be saved.")
        return

    history: list[AnyMessage] = []
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

        try:
            with SessionLocal() as session:
                turn: AgentTurn = answer_message(prompt, session, history)
        except Exception as error:
            print(f"Agent error ({type(error).__name__}): {error}")
            continue

        history = turn.messages
        _print_tool_activity(turn.activity_messages)
        print(f"Agent: {turn.answer}")
        print(f"Saved query #{turn.record_id} at {turn.output_at.isoformat()}")


if __name__ == "__main__":
    run_cli()
