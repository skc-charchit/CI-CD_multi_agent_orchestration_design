import os
from functools import lru_cache

from langchain.chat_models import init_chat_model
from langchain_core.tools import tool


# Define tools
@tool
def multiply(a: int, b: int) -> int:
    """Multiply `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a * b


@tool
def add(a: int, b: int) -> int:
    """Adds `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a + b


@tool
def divide(a: int, b: int) -> float:
    """Divide `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b


# Augment the LLM with tools
tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}


@lru_cache(maxsize=1)
def get_model_with_tools():
    """Create Gemini with the key exported by the local/deployment environment."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Run the app through direnv or configure "
            "the key in the deployment environment."
        )

    model = init_chat_model(
        "gemini-3.8-flash",
        model_provider="google_genai",
        temperature=0,
        api_key=api_key,
    )
    return model.bind_tools(tools)
