"""Tests for OpenAI model configuration and tool binding."""

from unittest.mock import Mock

import pytest
from backend.core.config import Settings
from backend.features.agentic_ai.tools import (
    ModelConfigurationError,
    get_model_with_tools,
    tools,
)
from pydantic import SecretStr


def test_model_factory_uses_configured_openai_settings(monkeypatch) -> None:
    fake_model = Mock()
    fake_model.bind_tools.return_value = "model with tools"
    chat_openai = Mock(return_value=fake_model)
    monkeypatch.setattr(
        "backend.features.agentic_ai.tools.ChatOpenAI",
        chat_openai,
    )
    config = Settings.model_construct(
        openai_api_key=SecretStr("test-openai-key"),
        openai_model="gpt-4o",
        openai_base_url="https://openai-compatible.example/v1",
        openai_max_tokens=512,
    )

    result = get_model_with_tools(config)

    assert result == "model with tools"
    chat_openai.assert_called_once_with(
        model="gpt-4o",
        temperature=0,
        api_key=SecretStr("test-openai-key"),
        base_url="https://openai-compatible.example/v1",
        max_completion_tokens=512,
    )
    fake_model.bind_tools.assert_called_once_with(tools)


def test_model_factory_reports_missing_openai_api_key() -> None:
    config = Settings.model_construct(
        openai_api_key=None,
        openai_model="gpt-4o",
        openai_base_url=None,
    )

    with pytest.raises(ModelConfigurationError, match="OPENAI_API_KEY is not set"):
        get_model_with_tools(config)
