from __future__ import annotations

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
