"""Optional LLM backend integration with explicit AI opt-in."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional


def _is_true(value: str) -> bool:
    """Return ``True`` when a string value represents an enabled flag."""
    return value.strip().lower() in {"1", "true", "yes", "on"}


class LLMBackend:
    """Common backend interface for optional text generation providers."""

    name = "base"

    def is_available(self) -> bool:
        """Return backend readiness state."""
        return False

    def generate(
        self, prompt: str, max_tokens: int = 400, temperature: float = 0.2
    ) -> str:
        """Generate text from prompt content."""
        raise NotImplementedError


class MockBackend(LLMBackend):
    """Always-available deterministic fallback backend."""

    name = "mock"

    def is_available(self) -> bool:
        return True

    def generate(
        self, prompt: str, max_tokens: int = 400, temperature: float = 0.2
    ) -> str:
        preview = prompt.strip().splitlines()[0] if prompt.strip() else "request"
        return (
            "Fallback suggestion (mock backend): create basic, edge-case, and error-path "
            f"tests for: {preview[:120]}"
        )


@dataclass
class AzureOpenAIBackend(LLMBackend):
    """Azure OpenAI chat-completions backend."""

    endpoint: str
    deployment: str
    api_key: str
    api_version: str = "2024-10-21"
    timeout_secs: float = 15.0

    name = "azure_openai"

    def is_available(self) -> bool:
        return bool(self.endpoint and self.deployment and self.api_key)

    def generate(
        self, prompt: str, max_tokens: int = 400, temperature: float = 0.2
    ) -> str:
        if not self.is_available():
            raise RuntimeError("Azure OpenAI backend is not configured")

        base = self.endpoint.rstrip("/")
        url = (
            f"{base}/openai/deployments/{self.deployment}/chat/completions"
            f"?api-version={self.api_version}"
        )
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "You generate concise Python testing suggestions.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "api-key": self.api_key,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_secs) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Azure OpenAI request failed: {exc}") from exc

        choices = body.get("choices", []) if isinstance(body, dict) else []
        if not choices:
            raise RuntimeError("Azure OpenAI response has no choices")
        message = choices[0].get("message", {})
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("Azure OpenAI response missing message content")
        return content.strip()


class LLMClient:
    """LLM wrapper with deterministic fallback behavior."""

    def __init__(
        self, backend: LLMBackend, fallback: Optional[LLMBackend] = None
    ) -> None:
        self._backend = backend
        self._fallback = fallback or MockBackend()

    @property
    def backend_name(self) -> str:
        """Return active backend name."""
        if self._backend.is_available():
            return self._backend.name
        return self._fallback.name

    @property
    def ai_enabled(self) -> bool:
        """Return ``True`` when non-mock backend is active and available."""
        return self._backend.name != "mock" and self._backend.is_available()

    def generate_test_cases(self, source_code: str, function_name: str) -> str:
        """Generate test-case guidance for a function source block."""
        prompt = (
            "Generate concise pytest test ideas for function "
            f"'{function_name}'. Include happy path, edge cases, and error cases.\n\n"
            f"Source:\n{source_code[:2500]}"
        )
        try:
            if self._backend.is_available():
                return self._backend.generate(prompt)
        except RuntimeError:
            pass
        return self._fallback.generate(prompt)


def get_llm(backend_type: str = "mock", use_ai: bool = False) -> LLMClient:
    """Return configured LLM client honoring explicit AI opt-in semantics."""
    ai_flag = _is_true(os.environ.get("CIV_AI_ENABLE", "false"))
    if not use_ai or not ai_flag:
        return LLMClient(MockBackend())

    normalized = backend_type.strip().lower() if backend_type else "mock"
    if normalized == "azure_openai":
        backend = AzureOpenAIBackend(
            endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
            deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT", ""),
            api_key=os.environ.get("AZURE_OPENAI_API_KEY", ""),
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        )
        return LLMClient(backend=backend, fallback=MockBackend())

    return LLMClient(MockBackend())
