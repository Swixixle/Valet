from __future__ import annotations

import os
from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMClient(Protocol):
    def generate(self, system: str, user: str) -> str: ...


class NullLLMClient:
    """Placeholder LLM client. Replace with a real implementation when LLM is wired."""

    def generate(self, system: str, user: str) -> str:  # noqa: ARG002
        raise NotImplementedError(
            "No LLM client configured. Wire a real LLMClient to enable generation."
        )


class _OpenAIClient:
    def __init__(self, api_key: str, model: str = "gpt-4o") -> None:
        import openai  # type: ignore[import-untyped]

        self._client = openai.OpenAI(api_key=api_key)
        self._model = model

    def generate(self, system: str, user: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content or ""


class _AnthropicClient:
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022") -> None:
        import anthropic  # type: ignore[import-untyped]

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def generate(self, system: str, user: str) -> str:
        message = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        block = message.content[0]
        return block.text if hasattr(block, "text") else str(block)


def get_llm_client() -> LLMClient:
    """Return a configured LLM client based on environment variables."""
    provider = os.environ.get("LLM_PROVIDER", "").strip().lower()
    if provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise OSError("OPENAI_API_KEY is not set.")
        return _OpenAIClient(api_key=api_key)
    if provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise OSError("ANTHROPIC_API_KEY is not set.")
        return _AnthropicClient(api_key=api_key)
    raise NotImplementedError(
        "No LLM provider configured. Set LLM_PROVIDER to 'openai' or 'anthropic'."
    )


def call_llm(system_prompt: str, user_prompt: str) -> str:
    """
    Call the configured LLM.
    Reads LLM_PROVIDER, OPENAI_API_KEY, and ANTHROPIC_API_KEY from environment.
    Raises NotImplementedError if no provider is configured.
    """
    client = get_llm_client()
    return client.generate(system=system_prompt, user=user_prompt)
