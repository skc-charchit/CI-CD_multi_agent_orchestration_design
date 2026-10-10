from backend.core.config import Settings, get_settings
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


class ModelConfigurationError(RuntimeError):
    """Raised when required model-provider configuration is missing."""


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


def get_model_with_tools(config: Settings | None = None):
    """Create the configured OpenAI model bound to the supported tools."""
    model_config = config or get_settings()
    if model_config.openai_api_key is None:
        raise ModelConfigurationError(
            "OPENAI_API_KEY is not set. Run the app through direnv or configure "
            "the key in the deployment environment."
        )

    model = ChatOpenAI(
        model=model_config.openai_model,
        temperature=0,
        api_key=model_config.openai_api_key,
        base_url=model_config.openai_base_url,
        max_completion_tokens=model_config.openai_max_tokens,
    )
    return model.bind_tools(tools)
