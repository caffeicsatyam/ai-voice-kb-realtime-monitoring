"""
ADK Tool: Nudge Emission
Applies confidence thresholds, cooldown, deduplication, priority, and expiry to nudges.
"""
import json
import time
from datetime import datetime
from typing import Optional


# Nudge state for session management
class NudgeState:
    """Tracks nudge history for duplicate suppression and cooldowns."""
    
    def __init__(self):
        self.emitted_nudges = []  # list of (signal_type, timestamp, nudge_text)
        self.last_nudge_time = {}  # signal_type -> last emit timestamp
        self.nudge_counts = {}  # signal_type -> count
    
    def can_emit(self, signal_type: str, cooldown_seconds: int = 15) -> bool:
        """Check if a nudge of this type can be emitted (not in cooldown)."""
        last_time = self.last_nudge_time.get(signal_type)
        if last_time is None:
            return True
        return (time.time() - last_time) >= cooldown_seconds
    
    def is_duplicate(self, signal_type: str, nudge_text: str) -> bool:
        """Check if this exact nudge was already emitted."""
        for prev_type, _, prev_text in self.emitted_nudges:
            if prev_type == signal_type and prev_text == nudge_text:
                return True
        return False
    
    def record(self, signal_type: str, nudge_text: str):
        """Record an emitted nudge."""
        now = time.time()
        self.emitted_nudges.append((signal_type, now, nudge_text))
        self.last_nudge_time[signal_type] = now
        self.nudge_counts[signal_type] = self.nudge_counts.get(signal_type, 0) + 1


# Global nudge state (per-session in production)
_state = NudgeState()


# Nudge templates by signal type
NUDGE_TEMPLATES = {
    "missed_cross_sell": {
        "priority": "medium",
        "template": "Consider mentioning {product}  customer may benefit from additional coverage or financial products.",
        "default_product": "insurance or savings products",
        "expires_after_seconds": 45,
    },
    "missing_disclosure": {
        "priority": "high",
        "template": " Add disclosure: {disclaimer}",
        "default_disclaimer": "Final approval is subject to document verification. Terms and conditions apply.",
        "expires_after_seconds": 30,
    },
    "frustration": {
        "priority": "high",
        "template": " Customer appears frustrated. Slow down, acknowledge their concern, and offer to help resolve the issue.",
        "expires_after_seconds": 60,
    },
    "payment_difficulty": {
        "priority": "medium",
        "template": "Customer indicates payment concern. Consider discussing flexible repayment options or lower loan amounts.",
        "expires_after_seconds": 45,
    },
    "callback_need": {
        "priority": "low",
        "template": "Customer wants to think about it. Offer to schedule a specific callback time.",
        "expires_after_seconds": 60,
    },
    "noisy_segment": {
        "priority": "low",
        "template": "Audio quality issue detected. Suppress low-confidence analysis for this segment.",
        "expires_after_seconds": 15,
    },
}

PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def emit_nudge(
    signal_type: str,
    confidence: float,
    evidence: Optional[str] = None,
    call_timestamp: Optional[str] = None,
    confidence_threshold: float = 0.7,
    cooldown_seconds: int = 15,
    max_per_type: int = 3,
) -> str:
    """
    Generate a nudge from a detected signal, applying quality controls.
    
    This tool takes a detected signal and decides whether to emit a nudge,
    applying confidence thresholds, cooldown periods, duplicate suppression,
    and per-type limits.
    
    Args:
        signal_type: Type of signal detected (e.g., "frustration", "missing_disclosure").
        confidence: Confidence score of the signal (0.0 to 1.0).
        evidence: The text evidence that triggered the signal.
        call_timestamp: Current position in the call.
        confidence_threshold: Minimum confidence to emit (default 0.7).
        cooldown_seconds: Minimum seconds between nudges of same type (default 15).
        max_per_type: Maximum nudges of same type per call (default 3).
    
    Returns:
        JSON with the nudge (if emitted) or suppression reason.
    """
    global _state
    
    template = NUDGE_TEMPLATES.get(signal_type, {})
    
    # Check 1: Confidence threshold
    if confidence < confidence_threshold:
        return json.dumps({
            "emitted": False,
            "reason": "below_confidence_threshold",
            "signal_type": signal_type,
            "confidence": confidence,
            "threshold": confidence_threshold,
        })
    
    # Check 2: Noisy segment suppression
    if signal_type == "noisy_segment":
        _state.record(signal_type, "noisy_segment")
        return json.dumps({
            "emitted": False,
            "reason": "noisy_segment_detected",
            "signal_type": signal_type,
            "note": "Suppressing other nudges during noisy/ambiguous audio.",
        })
    
    # Check 3: Cooldown
    if not _state.can_emit(signal_type, cooldown_seconds):
        return json.dumps({
            "emitted": False,
            "reason": "cooldown_active",
            "signal_type": signal_type,
            "cooldown_seconds": cooldown_seconds,
        })
    
    # Check 4: Per-type limit
    if _state.nudge_counts.get(signal_type, 0) >= max_per_type:
        return json.dumps({
            "emitted": False,
            "reason": "max_per_type_reached",
            "signal_type": signal_type,
            "max_per_type": max_per_type,
        })
    
    # Build nudge text
    nudge_text = template.get("template", f"Signal detected: {signal_type}")
    if "{product}" in nudge_text:
        nudge_text = nudge_text.format(product=template.get("default_product", "related products"))
    if "{disclaimer}" in nudge_text:
        nudge_text = nudge_text.format(disclaimer=template.get("default_disclaimer", "Terms apply."))
    
    # Check 5: Duplicate suppression
    if _state.is_duplicate(signal_type, nudge_text):
        return json.dumps({
            "emitted": False,
            "reason": "duplicate_suppressed",
            "signal_type": signal_type,
        })
    
    # Emit the nudge
    _state.record(signal_type, nudge_text)
    
    nudge = {
        "emitted": True,
        "timestamp": call_timestamp or datetime.now().strftime("%H:%M:%S"),
        "signal": signal_type,
        "priority": template.get("priority", "medium"),
        "confidence": round(confidence, 2),
        "nudge": nudge_text,
        "evidence": evidence,
        "expires_after_seconds": template.get("expires_after_seconds", 30),
        "nudge_count_for_type": _state.nudge_counts.get(signal_type, 1),
    }
    
    return json.dumps(nudge, indent=2)


def reset_nudge_state():
    """Reset nudge state for a new call/session."""
    global _state
    _state = NudgeState()


if __name__ == "__main__":
    reset_nudge_state()
    
    # Test: emit a frustration nudge
    print("=== Frustration nudge ===")
    print(emit_nudge("frustration", 0.85, "customer said 'this is so frustrating'"))
    
    # Test: duplicate suppression
    print("\n=== Duplicate attempt ===")
    print(emit_nudge("frustration", 0.85, "same frustration signal"))
    
    # Test: below threshold
    print("\n=== Below threshold ===")
    print(emit_nudge("missed_cross_sell", 0.5))
    
    # Test: noisy segment
    print("\n=== Noisy segment ===")
    print(emit_nudge("noisy_segment", 0.9, "[inaudible]"))

