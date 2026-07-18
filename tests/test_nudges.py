"""
Real-Time Nudge Tests (Q4)
Tests the 4 required nudge scenarios plus quality controls.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from adk_app.tools.detect_signals import detect_signals
from adk_app.tools.emit_nudge import emit_nudge, reset_nudge_state


class TestNudgeSignals:
    """Test signal detection for required scenarios."""

    def test_missed_cross_sell(self):
        """Scenario 1: Missed cross-sell opportunity emits useful nudge."""
        # Customer says they only want the loan, nothing else
        chunk = "I just need the loan, not interested in anything else like insurance or credit cards."
        
        result = json.loads(detect_signals(chunk, agent_or_customer="customer"))
        
        signals = result["signals"]
        assert len(signals) > 0, "No signals detected for missed cross-sell"
        
        cross_sell = [s for s in signals if s["signal_type"] == "missed_cross_sell"]
        assert len(cross_sell) > 0, f"Expected missed_cross_sell signal, got: {[s['signal_type'] for s in signals]}"
        
        print(f"\n--- Missed Cross-Sell Test ---")
        print(f"Input: {chunk}")
        print(f"Signal: {cross_sell[0]['signal_type']}")
        print(f"Confidence: {cross_sell[0]['confidence']}")
        print(f"Evidence: {cross_sell[0]['evidence']}")
        print(f"Verdict: PASS")

    def test_skipped_disclosure(self):
        """Scenario 2: Skipped disclosure/risky statement emits compliance nudge."""
        # Agent makes a promise without disclaimer
        chunk = "Yes, your loan is definitely approved! No additional fees at all."
        
        result = json.loads(detect_signals(chunk, agent_or_customer="agent"))
        
        signals = result["signals"]
        assert len(signals) > 0, "No signals detected for skipped disclosure"
        
        disclosure = [s for s in signals if s["signal_type"] == "missing_disclosure"]
        assert len(disclosure) > 0, f"Expected missing_disclosure signal, got: {[s['signal_type'] for s in signals]}"
        
        print(f"\n--- Skipped Disclosure Test ---")
        print(f"Input: {chunk}")
        print(f"Signal: {disclosure[0]['signal_type']}")
        print(f"Confidence: {disclosure[0]['confidence']}")
        print(f"Evidence: {disclosure[0]['evidence']}")
        print(f"Verdict: PASS")

    def test_rising_frustration(self):
        """Scenario 3: Rising frustration emits empathy/slowdown nudge."""
        chunk = "I already told you my details three times! This is so frustrating. How many times do I need to explain?"
        
        result = json.loads(detect_signals(chunk, agent_or_customer="customer"))
        
        signals = result["signals"]
        assert len(signals) > 0, "No signals detected for frustration"
        
        frustration = [s for s in signals if s["signal_type"] == "frustration"]
        assert len(frustration) > 0, f"Expected frustration signal, got: {[s['signal_type'] for s in signals]}"
        assert frustration[0]["confidence"] >= 0.7, f"Frustration confidence too low: {frustration[0]['confidence']}"
        
        print(f"\n--- Rising Frustration Test ---")
        print(f"Input: {chunk}")
        print(f"Signal: {frustration[0]['signal_type']}")
        print(f"Confidence: {frustration[0]['confidence']}")
        print(f"Evidence: {frustration[0]['evidence']}")
        print(f"Verdict: PASS")

    def test_noisy_audio_suppression(self):
        """Scenario 4: Noisy/ambiguous audio suppresses unnecessary nudges."""
        chunk = "[inaudible] ...can't hear you... [static] ...bad connection... breaking up..."
        
        result = json.loads(detect_signals(chunk, agent_or_customer="customer"))
        
        signals = result["signals"]
        noisy = [s for s in signals if s["signal_type"] == "noisy_segment"]
        assert len(noisy) > 0, f"Expected noisy_segment signal, got: {[s['signal_type'] for s in signals]}"
        
        # Now test that emit_nudge suppresses for noisy segment
        reset_nudge_state()
        nudge_result = json.loads(emit_nudge(
            signal_type="noisy_segment",
            confidence=0.9,
            evidence="[inaudible]",
        ))
        assert nudge_result.get("emitted") is False, "Noisy segment should not emit a nudge"
        assert "noisy_segment" in nudge_result.get("reason", ""), f"Expected noisy reason, got: {nudge_result.get('reason')}"
        
        print(f"\n--- Noisy Audio Suppression Test ---")
        print(f"Input: {chunk}")
        print(f"Signal: noisy_segment detected")
        print(f"Nudge emitted: {nudge_result.get('emitted')} (expected: False)")
        print(f"Suppression reason: {nudge_result.get('reason')}")
        print(f"Verdict: PASS")


class TestNudgeControls:
    """Test nudge quality controls: confidence, cooldown, dedup, limits."""

    def setup_method(self):
        """Reset nudge state before each test."""
        reset_nudge_state()

    def test_confidence_threshold(self):
        """Nudges below confidence threshold are suppressed."""
        result = json.loads(emit_nudge("frustration", confidence=0.5, confidence_threshold=0.7))
        assert result["emitted"] is False
        assert result["reason"] == "below_confidence_threshold"

    def test_above_confidence_threshold(self):
        """Nudges above threshold are emitted."""
        result = json.loads(emit_nudge("frustration", confidence=0.85, confidence_threshold=0.7))
        assert result["emitted"] is True
        assert result["signal"] == "frustration"
        assert "priority" in result

    def test_duplicate_suppression(self):
        """Same nudge type/text is suppressed on second emission."""
        # First emission
        r1 = json.loads(emit_nudge("frustration", confidence=0.85))
        assert r1["emitted"] is True
        
        # Second emission (duplicate) - need to bypass cooldown
        import time
        time.sleep(0.01)
        # Since cooldown is 15s, this should be caught by duplicate check if we wait
        # For testing, we check that the state tracks it
        r2 = json.loads(emit_nudge("frustration", confidence=0.85, cooldown_seconds=0))
        assert r2["emitted"] is False
        assert r2["reason"] == "duplicate_suppressed"

    def test_nudge_expiry_field(self):
        """Emitted nudges include an expiry time."""
        result = json.loads(emit_nudge("missing_disclosure", confidence=0.9))
        assert result["emitted"] is True
        assert "expires_after_seconds" in result
        assert result["expires_after_seconds"] > 0

    def test_priority_levels(self):
        """Different signal types have different priority levels."""
        reset_nudge_state()
        r1 = json.loads(emit_nudge("frustration", confidence=0.9))
        assert r1["priority"] == "high"
        
        reset_nudge_state()
        r2 = json.loads(emit_nudge("callback_need", confidence=0.9))
        assert r2["priority"] == "low"
        
        reset_nudge_state()
        r3 = json.loads(emit_nudge("missed_cross_sell", confidence=0.9))
        assert r3["priority"] == "medium"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
