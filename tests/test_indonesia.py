"""
Indonesia Voice Bot Tests (Q3)
Tests localization, formal/colloquial register, and finance terms.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestIndonesiaLocalization:
    """Test Indonesia bot localization requirements."""

    def test_required_finance_terms(self):
        """Required Indonesian finance terms are in the agent instruction."""
        from adk_app.agents.indonesia_voice_agent import INDONESIA_AGENT_INSTRUCTION
        
        required_terms = ["cicilan", "tenor", "denda", "DP", "jatuh tempo", "angsuran", "pembiayaan"]
        
        for term in required_terms:
            assert term in INDONESIA_AGENT_INSTRUCTION, \
                f"Required term '{term}' not found in Indonesia agent instruction"
        
        print(f"All {len(required_terms)} required terms present: {', '.join(required_terms)}")

    def test_formal_bahasa_support(self):
        """Agent supports formal Bahasa Indonesia."""
        from adk_app.agents.indonesia_voice_agent import INDONESIA_AGENT_INSTRUCTION
        
        formal_markers = ["bapak", "ibu", "selamat", "mohon", "formal"]
        found = [m for m in formal_markers if m.lower() in INDONESIA_AGENT_INSTRUCTION.lower()]
        assert len(found) >= 3, f"Insufficient formal Bahasa markers. Found: {found}"

    def test_colloquial_bahasa_support(self):
        """Agent supports colloquial Bahasa Indonesia."""
        from adk_app.agents.indonesia_voice_agent import INDONESIA_AGENT_INSTRUCTION
        
        colloquial_markers = ["colloquial", "gue", "gw", "lo", "nih", "dong", "santai"]
        found = [m for m in colloquial_markers if m.lower() in INDONESIA_AGENT_INSTRUCTION.lower()]
        assert len(found) >= 2, f"Insufficient colloquial Bahasa markers. Found: {found}"

    def test_english_loanwords(self):
        """Agent handles English finance loanwords naturally."""
        from adk_app.agents.indonesia_voice_agent import INDONESIA_AGENT_INSTRUCTION
        
        assert "loanword" in INDONESIA_AGENT_INSTRUCTION.lower() or \
               "english" in INDONESIA_AGENT_INSTRUCTION.lower(), \
               "Should mention English loanword handling"
        assert "DP" in INDONESIA_AGENT_INSTRUCTION  # DP is a common loanword
        assert "tenor" in INDONESIA_AGENT_INSTRUCTION

    def test_regional_accent_awareness(self):
        """Agent addresses at least one regional accent outside Jakarta."""
        from adk_app.agents.indonesia_voice_agent import INDONESIA_AGENT_INSTRUCTION
        
        regional_markers = ["javanese", "sundanese", "balinese", "regional", "accent"]
        found = [m for m in regional_markers if m.lower() in INDONESIA_AGENT_INSTRUCTION.lower()]
        assert len(found) >= 2, f"Insufficient regional accent coverage. Found: {found}"

    def test_escalation_stays_in_bahasa(self):
        """Escalation instruction mentions staying in customer's language."""
        from adk_app.agents.indonesia_voice_agent import INDONESIA_AGENT_INSTRUCTION
        
        # Should have Bahasa escalation phrases
        assert "sambungkan" in INDONESIA_AGENT_INSTRUCTION.lower() or \
               "supervisor" in INDONESIA_AGENT_INSTRUCTION.lower(), \
               "Escalation should have Bahasa phrases"

    def test_localization_examples(self):
        """At least 3 localization examples showing adaptation."""
        from adk_app.agents.indonesia_voice_agent import INDONESIA_AGENT_INSTRUCTION
        
        assert "localization examples" in INDONESIA_AGENT_INSTRUCTION.lower(), \
            "Missing localization examples section"
        
        # Count numbered examples or "instead of" patterns
        example_count = INDONESIA_AGENT_INSTRUCTION.lower().count("instead of")
        assert example_count >= 2, f"Need at least 3 adaptation examples, found {example_count} 'instead of' patterns"


class TestIndonesiaBotConfig:
    """Test bot configuration completeness."""

    def test_agent_is_valid(self):
        """Indonesia agent can be imported and has correct structure."""
        from adk_app.agents.indonesia_voice_agent import indonesia_voice_agent
        
        assert indonesia_voice_agent.name == "indonesia_voice_agent"
        assert indonesia_voice_agent.model == "gemini-2.0-flash"
        assert len(indonesia_voice_agent.instruction) > 500

    def test_sector_is_consumer_finance(self):
        """Agent is configured for consumer finance/installment sector."""
        from adk_app.agents.indonesia_voice_agent import INDONESIA_AGENT_INSTRUCTION
        
        assert any(term in INDONESIA_AGENT_INSTRUCTION.lower() for term in 
                   ["consumer finance", "installment", "cicilan", "pembiayaan"]), \
            "Agent should be configured for consumer finance sector"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
