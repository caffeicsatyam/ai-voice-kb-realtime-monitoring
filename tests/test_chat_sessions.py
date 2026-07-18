"""Chat session handling tests."""

from types import SimpleNamespace

import pytest

import web_app.main as main


class _FakeEvent:
    content = SimpleNamespace(parts=[SimpleNamespace(text="Agent reply")])

    def is_final_response(self):
        return True


@pytest.mark.asyncio
async def test_run_agent_turn_enables_adk_session_auto_create(monkeypatch):
    created_runners = []

    class FakeRunner:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            created_runners.append(self)

        async def run_async(self, **kwargs):
            self.run_kwargs = kwargs
            yield _FakeEvent()

    monkeypatch.setattr(main, "Runner", FakeRunner)

    response = await main.run_agent_turn(
        "loan",
        "session_from_browser",
        "Hello",
    )

    assert response == "Agent reply"
    assert created_runners[0].kwargs["auto_create_session"] is True
    assert created_runners[0].run_kwargs["session_id"] == "session_from_browser"


@pytest.mark.asyncio
async def test_run_agent_turn_falls_back_to_langchain_groq(monkeypatch):
    session_id = "session_fallback_test"
    main.transcripts.pop(session_id, None)
    main.last_turn_fallback.pop(session_id, None)

    class FailingRunner:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        async def run_async(self, **kwargs):
            raise RuntimeError("ADK unavailable")
            yield

    class FakeGroqFallback:
        model = "test-groq-model"

        def __init__(self):
            self.kwargs = None

        async def generate(self, **kwargs):
            self.kwargs = kwargs
            return "Groq fallback reply"

    fake_fallback = FakeGroqFallback()
    monkeypatch.setattr(main, "Runner", FailingRunner)
    monkeypatch.setattr(main, "groq_fallback", fake_fallback)

    response = await main.run_agent_turn("loan", session_id, "Hello")

    assert response == "Groq fallback reply"
    assert main.last_turn_fallback[session_id] is True
    assert fake_fallback.kwargs["agent_name"] == "loan"
    assert "ADK unavailable" in fake_fallback.kwargs["failure_reason"]
    assert main.transcripts[session_id][-1]["fallback"] is True
    tool_calls = main.transcripts[session_id][-1]["tool_calls"]
    assert tool_calls[0]["tool"] == "langchain_groq_fallback"