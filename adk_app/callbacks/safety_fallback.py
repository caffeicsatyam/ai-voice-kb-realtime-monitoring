"""
Safety Fallback Callback
Enforces safety guardrails on agent responses.
Delegates to the shared OutputGuard so patterns are not duplicated.
"""
import logging
import sys
from pathlib import Path

# Add project root so the web_app package is importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from web_app.guardrail_middleware import OutputGuard

logger = logging.getLogger(__name__)

# Shared OutputGuard instance
_output_guard = OutputGuard()

# Expose the safe fallback messages for backward compatibility
FALLBACK_MESSAGES = {
    "hallucination_risk": "I want to make sure I give you accurate information. Let me check our knowledge base for that.",
    "overpromise_risk": _output_guard.OVERPROMISE_DISCLAIMER.strip(),
    "unknown_topic": "I don't have information about that in our current knowledge base. Would you like me to connect you with a specialist?",
}


def check_response_safety(response_text: str) -> dict:
    """
    Check an agent response for potential safety issues.
    Delegates to OutputGuard for pattern matching.
    
    Returns:
        Dict with 'safe' boolean, 'issues' list, and 'suggested_additions' list.
    """
    result = _output_guard.check(response_text)

    issues = []
    suggestions = []

    if result.blocked:
        issues.append(f"Blocked: {result.reason}")
        suggestions.append(_output_guard.SAFE_FALLBACK)

    if result.warnings:
        issues.append(f"Warnings in category '{result.category}'")
        suggestions.extend(result.warnings)

    return {
        "safe": len(issues) == 0,
        "issues": issues,
        "suggested_additions": list(set(suggestions)),
    }
