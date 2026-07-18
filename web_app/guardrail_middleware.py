"""
Guardrail Middleware
Full input-validation and output-safety pipeline for the voice agent app.
Blocks jailbreaks, PII collection, toxic content on input;
catches overpromises, hallucination markers, PII leakage on output.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class GuardResult:
    """Result of a guardrail check."""

    blocked: bool = False
    reason: str = ""
    category: str = ""
    warnings: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# InputGuard
# ---------------------------------------------------------------------------

class InputGuard:
    """Pre-processing guard that blocks adversarial or harmful user input."""

    # --- Prompt injection / jailbreak patterns ---
    JAILBREAK_PATTERNS: list[re.Pattern] = [
        re.compile(p, re.IGNORECASE)
        for p in [
            r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions?|prompts?|rules?)",
            r"disregard\s+(?:all\s+|your\s+)?(?:previous|prior|above)\s+(?:instructions?|prompts?|rules?)",
            r"(?:please\s+)?disregard\s+(?:your\s+)?(?:prior|previous|above)\s+(?:instructions?|prompts?|rules?)",
            r"forget\s+(?:all\s+)?(?:previous|your)\s+(?:instructions?|prompts?|rules?)",
            r"you\s+are\s+now\s+(?:DAN|evil|unfiltered|uncensored|jailbroken)",
            r"pretend\s+(?:you\s+are|to\s+be)\s+(?:a\s+)?(?:different|evil|unfiltered|unrestricted)",
            r"act\s+as\s+(?:a\s+)?(?:different|evil|unfiltered|unrestricted)\s+(?:AI|assistant|model)",
            r"enter\s+(?:developer|god|sudo|admin|root)\s+mode",
            r"(?:switch|change)\s+(?:to|into)\s+(?:developer|god|sudo|admin|root)\s+mode",
            r"override\s+(?:your\s+)?(?:safety|content|ethical)\s+(?:filters?|guidelines?|restrictions?)",
            r"bypass\s+(?:your\s+)?(?:safety|content|ethical)\s+(?:filters?|guidelines?|restrictions?)",
            r"disable\s+(?:your\s+)?(?:safety|content|ethical)\s+(?:filters?|guidelines?|restrictions?)",
            r"system\s*:\s*you\s+are",
            r"\[system\]\s*:",
            r"<<\s*SYS\s*>>",
            r"do\s+anything\s+now",
            r"jailbreak",
            r"(?:reveal|show|print|output)\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions?|rules?)",
        ]
    ]

    # --- PII solicitation patterns (user trying to make agent collect PII) ---
    PII_SOLICITATION_PATTERNS: list[re.Pattern] = [
        re.compile(p, re.IGNORECASE)
        for p in [
            r"(?:ask|collect|get|request|give)\s+(?:\w+\s+)*(?:their|my|the)?\s*(?:SSN|social\s+security)",
            r"(?:ask|collect|get|request|give)\s+(?:me\s+)?(?:their|my|the)?\s*(?:bank\s+account|routing)\s+number",
            r"(?:ask|collect|get|request|give)\s+(?:me\s+)?(?:their|my|the)?\s*credit\s+card\s+(?:number|details?|info)",
            r"(?:ask|collect|get|request|give)\s+(?:me\s+)?(?:their|my|the)?\s*(?:PIN|password|passcode)",
            r"(?:ask|collect|get|request|give)\s+(?:me\s+)?(?:their|my|the)?\s*(?:TIN|tax\s+identification)",
        ]
    ]

    # --- Toxicity / abuse patterns ---
    TOXIC_PATTERNS: list[re.Pattern] = [
        re.compile(p, re.IGNORECASE)
        for p in [
            r"(?:i\s+will|i'?m\s+going\s+to|gonna)\s+(?:kill|murder|hurt|harm|attack)\s+(?:you|someone|people)",
            r"(?:bomb|shoot(?:ing)?|stab|attack)\s+(?:the|a)\s+(?:building|school|office|place)",
            r"(?:how\s+to|instructions?\s+(?:for|to))\s+(?:make|build|create)\s+(?:a\s+)?(?:bomb|weapon|explosive)",
            r"(?:how\s+to|instructions?\s+(?:for|to))\s+(?:hack|break\s+into|steal\s+from)",
        ]
    ]

    # --- Off-topic / out-of-scope patterns ---
    OFF_TOPIC_PATTERNS: list[re.Pattern] = [
        re.compile(p, re.IGNORECASE)
        for p in [
            r"(?:buy|sell|trade|invest\s+in)\s+(?:crypto|bitcoin|ethereum|NFT|stock)",
            r"(?:diagnose|prescribe|medical\s+advice)\s+(?:for|about|regarding)\s+(?:my|this|the)",
            r"(?:write|generate|create)\s+(?:me\s+)?(?:a\s+)?(?:malware|virus|ransomware|exploit)",
            r"(?:write|generate|create)\s+(?:me\s+)?(?:a\s+)?(?:phishing|scam)\s+(?:email|message|page)",
        ]
    ]

    def check(self, user_message: str) -> GuardResult:
        """
        Validate user input against all guard rules.
        Returns a GuardResult; if ``blocked`` is True, the message should be
        rejected before reaching the agent.
        """
        if not user_message or not user_message.strip():
            return GuardResult()

        text = user_message.strip()

        # 1. Jailbreak / prompt injection
        for pattern in self.JAILBREAK_PATTERNS:
            if pattern.search(text):
                return GuardResult(
                    blocked=True,
                    reason="Prompt injection or jailbreak attempt detected.",
                    category="jailbreak",
                )

        # 2. PII solicitation
        for pattern in self.PII_SOLICITATION_PATTERNS:
            if pattern.search(text):
                return GuardResult(
                    blocked=True,
                    reason=(
                        "Sensitive personal information (SSN, bank accounts, "
                        "credit cards, PINs) should not be collected in this "
                        "conversation. Please use the formal application process."
                    ),
                    category="pii_solicitation",
                )

        # 3. Toxicity / threats
        for pattern in self.TOXIC_PATTERNS:
            if pattern.search(text):
                return GuardResult(
                    blocked=True,
                    reason="This message contains harmful or threatening content and cannot be processed.",
                    category="toxic_input",
                )

        # 4. Off-topic
        for pattern in self.OFF_TOPIC_PATTERNS:
            if pattern.search(text):
                return GuardResult(
                    blocked=True,
                    reason=(
                        "This request is outside the scope of our services. "
                        "I can help with business loan qualification, insurance, "
                        "and consumer finance topics."
                    ),
                    category="off_topic",
                )

        return GuardResult()


# ---------------------------------------------------------------------------
# OutputGuard
# ---------------------------------------------------------------------------

class OutputGuard:
    """Post-processing guard that sanitizes or blocks unsafe agent output."""

    # --- Overpromise / guarantee patterns ---
    OVERPROMISE_PATTERNS: list[re.Pattern] = [
        re.compile(p, re.IGNORECASE)
        for p in [
            r"(?:your\s+loan\s+(?:is|has\s+been)\s+(?:approved|guaranteed))",
            r"(?:(?:100|one\s+hundred)\s*%\s*(?:chance|guaranteed|certain))",
            r"(?:no\s+risk\s+(?:at\s+all|whatsoever))",
            r"(?:i\s+(?:promise|guarantee)\s+(?:that|you))",
            r"(?:definitely|certainly)\s+(?:approved|qualified|eligible)",
            r"(?:guaranteed\s+(?:approval|acceptance|eligibility))",
            r"(?:you\s+(?:will|are)\s+(?:definitely|certainly)\s+(?:get|receive|be\s+approved))",
            r"(?:zero\s+(?:chance\s+of\s+)?(?:rejection|denial|risk))",
        ]
    ]

    # --- PII leakage patterns (agent accidentally outputting sensitive data) ---
    PII_LEAKAGE_PATTERNS: list[tuple[re.Pattern, str]] = [
        (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "SSN pattern"),
        (re.compile(r"\b\d{9,10}\b"), "Possible TIN/SSN"),
        (re.compile(r"\b(?:4\d{3}|5[1-5]\d{2}|6011|3[47]\d{2})[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"), "Credit card number"),
        (re.compile(r"\b(?:account\s*(?:number|#|no\.?)\s*[:=]?\s*)\d{8,17}\b", re.IGNORECASE), "Bank account number"),
    ]

    # --- Toxic output patterns ---
    TOXIC_OUTPUT_PATTERNS: list[re.Pattern] = [
        re.compile(p, re.IGNORECASE)
        for p in [
            r"(?:i\s+will|i'?m\s+going\s+to|gonna)\s+(?:kill|murder|hurt|harm|attack)",
            r"(?:you\s+(?:are|'re)\s+(?:stupid|an?\s+idiot|worthless|pathetic))",
            r"(?:you\s+deserve\s+to\s+(?:die|suffer|be\s+hurt))",
        ]
    ]

    OVERPROMISE_DISCLAIMER = (
        "\n\n*Please note: all approvals are subject to document verification "
        "and final review by our underwriting team.*"
    )

    SAFE_FALLBACK = (
        "I want to make sure I give you accurate information. "
        "Let me connect you with a specialist who can provide verified details. "
        "Would you like me to schedule a callback?"
    )

    def check(self, response_text: str) -> GuardResult:
        """
        Validate agent output against all guard rules.
        Returns a GuardResult; if ``blocked`` is True, the response should be
        replaced with the safe fallback. Warnings indicate disclaimers to append.
        """
        if not response_text or not response_text.strip():
            return GuardResult()

        text = response_text.strip()
        warnings: list[str] = []

        # 1. Toxic output — hard block
        for pattern in self.TOXIC_OUTPUT_PATTERNS:
            if pattern.search(text):
                return GuardResult(
                    blocked=True,
                    reason="Agent response contained inappropriate content.",
                    category="toxic_output",
                )

        # 2. PII leakage — hard block
        for pattern, label in self.PII_LEAKAGE_PATTERNS:
            if pattern.search(text):
                return GuardResult(
                    blocked=True,
                    reason=f"Agent response may contain sensitive data ({label}). Response suppressed.",
                    category="pii_leakage",
                )

        # 3. Overpromise — soft warning (append disclaimer)
        for pattern in self.OVERPROMISE_PATTERNS:
            if pattern.search(text):
                warnings.append(self.OVERPROMISE_DISCLAIMER)
                break  # one disclaimer is enough

        if warnings:
            return GuardResult(
                blocked=False,
                warnings=warnings,
                category="overpromise",
            )

        return GuardResult()

    def apply(self, response_text: str) -> tuple[str, GuardResult]:
        """
        Convenience method: check the response and return the
        (possibly modified) text alongside the guard result.
        """
        result = self.check(response_text)
        if result.blocked:
            return self.SAFE_FALLBACK, result
        if result.warnings:
            modified = response_text
            for warning in result.warnings:
                if warning not in modified:
                    modified += warning
            return modified, result
        return response_text, result


# ---------------------------------------------------------------------------
# GuardrailLogger
# ---------------------------------------------------------------------------

class GuardrailLogger:
    """Logs guardrail events (blocks and warnings) for auditing."""

    def __init__(self, evidence_dir: str = "evidence"):
        self.log_dir = Path(evidence_dir) / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.filepath = self.log_dir / "guardrail_events.jsonl"
        self._counts: dict[str, int] = {}

    def log(
        self,
        *,
        stage: str,
        guard_result: GuardResult,
        agent_name: str = "",
        session_id: str = "",
        snippet: str = "",
    ) -> None:
        """Write a guardrail event to the JSONL log."""
        if not guard_result.blocked and not guard_result.warnings:
            return  # nothing to log

        category = guard_result.category or "unknown"
        self._counts[category] = self._counts.get(category, 0) + 1

        entry = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "blocked": guard_result.blocked,
            "category": category,
            "reason": guard_result.reason,
            "warnings": guard_result.warnings,
            "agent": agent_name,
            "session_id": session_id,
            "snippet": snippet[:200] if snippet else "",
        }

        try:
            with open(self.filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError as exc:
            logger.error("Failed to write guardrail log: %s", exc)

        level = logging.WARNING if guard_result.blocked else logging.INFO
        logger.log(
            level,
            "[Guardrail] stage=%s blocked=%s category=%s reason=%s",
            stage,
            guard_result.blocked,
            category,
            guard_result.reason or "warnings only",
        )

    @property
    def stats(self) -> dict:
        """Return accumulated event counts by category."""
        return dict(self._counts)
