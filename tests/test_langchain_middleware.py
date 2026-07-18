"""LangChain Groq fallback middleware tests."""

import pytest

from web_app.langchain_middleware import (
    GroqFallbackUnavailable,
    LangChainGroqFallbackMiddleware,
)


@pytest.mark.asyncio
async def test_groq_fallback_requires_api_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    fallback = LangChainGroqFallbackMiddleware(api_key="")

    with pytest.raises(GroqFallbackUnavailable, match="GROQ_API_KEY"):
        await fallback.generate(
            agent_name="loan",
            session_id="session_missing_key",
            user_message="Hello",
        )


def test_groq_placeholder_key_is_not_configured():
    fallback = LangChainGroqFallbackMiddleware(api_key="your_groq_api_key_here")

    assert fallback.is_configured is False