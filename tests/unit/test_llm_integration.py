"""Unit tests for optional LLM backend integration."""

from civ_arcos.analysis.llm_integration import get_llm


def test_default_returns_mock_backend(monkeypatch):
    monkeypatch.delenv("CIV_AI_ENABLE", raising=False)
    client = get_llm(backend_type="azure_openai", use_ai=False)
    assert client.backend_name == "mock"
    assert client.ai_enabled is False


def test_opt_in_without_azure_config_falls_back_to_mock(monkeypatch):
    monkeypatch.setenv("CIV_AI_ENABLE", "true")
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)

    client = get_llm(backend_type="azure_openai", use_ai=True)
    assert client.backend_name == "mock"
    assert client.ai_enabled is False


def test_opt_in_with_azure_config_marks_backend_active(monkeypatch):
    monkeypatch.setenv("CIV_AI_ENABLE", "true")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")

    client = get_llm(backend_type="azure_openai", use_ai=True)
    assert client.backend_name == "azure_openai"
    assert client.ai_enabled is True
