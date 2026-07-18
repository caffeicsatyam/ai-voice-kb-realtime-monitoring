"""LangChain-powered Groq fallback for ADK agent failures."""

from __future__ import annotations

import os
from typing import Optional


class GroqFallbackUnavailable(RuntimeError):
    """Raised when the Groq fallback cannot be used."""


class LangChainGroqFallbackMiddleware:
    """Generate a safe fallback response through LangChain and Groq."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> None:
        self.api_key = (api_key or os.environ.get("GROQ_API_KEY", "")).strip()
        if self.api_key.lower() in {"your_groq_api_key_here", "your_api_key_here"}:
            self.api_key = ""
        self.model = model or os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.temperature = temperature if temperature is not None else float(
            os.environ.get("GROQ_TEMPERATURE", "0.2")
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def generate(
        self,
        *,
        agent_name: str,
        user_message: str,
        session_id: str,
        failure_reason: str = "",
    ) -> str:
        """Return a conservative Groq response when the ADK path fails."""
        if not self.is_configured:
            raise GroqFallbackUnavailable("GROQ_API_KEY is not configured.")

        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from langchain_groq import ChatGroq
        except ImportError as exc:
            raise GroqFallbackUnavailable(
                "LangChain Groq fallback dependencies are missing. "
                "Install langchain-core and langchain-groq."
            ) from exc

        llm = ChatGroq(
            model=self.model,
            temperature=self.temperature,
            api_key=self.api_key,
        )
        result = await llm.ainvoke(
            [
                SystemMessage(
                    content=self._system_prompt(
                        agent_name=agent_name,
                        session_id=session_id,
                        failure_reason=failure_reason,
                    )
                ),
                HumanMessage(content=user_message),
            ]
        )
        content = getattr(result, "content", "")
        if isinstance(content, list):
            content = "\n".join(str(part) for part in content)
        return str(content).strip()

    def _system_prompt(
        self,
        *,
        agent_name: str,
        session_id: str,
        failure_reason: str,
    ) -> str:
        base = (
            "You are a backup AI response path for a FastAPI voice-agent demo. "
            "The primary Google ADK agent failed, so respond helpfully but conservatively. "
            "Do not claim that tools, CRM actions, live account lookups, or policy retrieval succeeded. "
            "Do not invent rates, approvals, exact eligibility decisions, customer records, or citations. "
            "If a tool-backed action is needed, explain that a specialist or the primary system should confirm it. "
            f"Session id: {session_id}. Primary failure: {failure_reason or 'not provided'}."
        )

        agent_guidance = {
            "loan": (
                "You are backing up QuickFund's small-business loan qualification agent. "
                "You may collect non-sensitive qualification details, answer general process questions, "
                "and offer a callback/escalation. For documents, pricing, product rules, or eligibility, "
                "avoid exact claims unless the user already supplied the information."
            ),
            "philippines": (
                "You are backing up a Philippine bancassurance renewal reminder agent. "
                "Use English, Filipino, or Taglish to match the customer. Stay polite and use po/opo when speaking Filipino. "
                "Never reveal or request sensitive policy, banking, PIN, or full identity details."
            ),
            "indonesia": (
                "You are backing up an Indonesian consumer-finance installment reminder agent. "
                "Respond in Bahasa Indonesia unless the customer uses English. Stay respectful and solution-oriented. "
                "Never threaten legal action or request sensitive account credentials."
            ),
            "nudge": (
                "You are backing up a real-time call nudge analyzer. Keep the response very short. "
                "Only mention obvious signals from the user's transcript chunk and say when deterministic checks are unavailable."
            ),
        }
        return f"{base}\n\n{agent_guidance.get(agent_name, agent_guidance['loan'])}"