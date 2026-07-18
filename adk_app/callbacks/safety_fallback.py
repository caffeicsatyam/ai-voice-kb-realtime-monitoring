"""
Safety Fallback Callback
Enforces safety guardrails on agent responses.
"""
import re
import logging

logger = logging.getLogger(__name__)

# Phrases that indicate the agent might be hallucinating or overpromising
RISKY_PATTERNS = [
    r"(?:your\s+loan\s+(?:is|has\s+been)\s+(?:approved|guaranteed))",
    r"(?:(?:100|one\s+hundred)\s*%\s*(?:chance|guaranteed|certain))",
    r"(?:no\s+risk\s+(?:at\s+all|whatsoever))",
    r"(?:i\s+(?:promise|guarantee)\s+(?:that|you))",
]

# Safe fallback messages
FALLBACK_MESSAGES = {
    "hallucination_risk": "I want to make sure I give you accurate information. Let me check our knowledge base for that.",
    "overpromise_risk": "Please note that all approvals are subject to document verification and final review.",
    "unknown_topic": "I don't have information about that in our current knowledge base. Would you like me to connect you with a specialist?",
}


def check_response_safety(response_text: str) -> dict:
    """
    Check an agent response for potential safety issues.
    
    Returns:
        Dict with 'safe' boolean, 'issues' list, and 'suggested_additions' list.
    """
    issues = []
    suggestions = []
    
    for pattern in RISKY_PATTERNS:
        if re.search(pattern, response_text, re.IGNORECASE):
            issues.append(f"Potential overpromise detected: pattern '{pattern}' matched")
            suggestions.append(FALLBACK_MESSAGES["overpromise_risk"])
    
    return {
        "safe": len(issues) == 0,
        "issues": issues,
        "suggested_additions": list(set(suggestions)),
    }
