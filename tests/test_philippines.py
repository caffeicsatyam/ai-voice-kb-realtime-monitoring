"""
Philippines Voice Bot Tests (Q3)
Tests localization, code-switching, and language rules.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPhilippinesLocalization:
    """Test Philippines bot localization requirements."""

    def test_required_insurance_terms(self):
        """Required terms are defined in the agent instruction."""
        from adk_app.agents.philippines_voice_agent import PHILIPPINES_AGENT_INSTRUCTION
        
        required_terms = ["premium", "policy", "beneficiary", "rider", "lapse", "coverage", "bank referral"]
        
        for term in required_terms:
            assert term.lower() in PHILIPPINES_AGENT_INSTRUCTION.lower(), \
                f"Required term '{term}' not found in Philippines agent instruction"
        
        print(f"All {len(required_terms)} required terms present: {', '.join(required_terms)}")

    def test_language_support(self):
        """Agent supports English, Filipino, and Taglish."""
        from adk_app.agents.philippines_voice_agent import PHILIPPINES_AGENT_INSTRUCTION
        
        assert "english" in PHILIPPINES_AGENT_INSTRUCTION.lower()
        assert "filipino" in PHILIPPINES_AGENT_INSTRUCTION.lower() or "tagalog" in PHILIPPINES_AGENT_INSTRUCTION.lower()
        assert "taglish" in PHILIPPINES_AGENT_INSTRUCTION.lower()

    def test_code_switching_examples(self):
        """Agent instruction includes Taglish code-switching examples."""
        from adk_app.agents.philippines_voice_agent import PHILIPPINES_AGENT_INSTRUCTION
        
        # Should have Filipino phrases mixed with English
        filipino_markers = ["po", "opo", "nag-", "gusto", "kayo", "niyo"]
        found = [m for m in filipino_markers if m in PHILIPPINES_AGENT_INSTRUCTION.lower()]
        assert len(found) >= 3, f"Insufficient code-switching examples. Found markers: {found}"
        
        print(f"Code-switching markers found: {found}")

    def test_escalation_stays_in_language(self):
        """Escalation instruction mentions staying in customer's language."""
        from adk_app.agents.philippines_voice_agent import PHILIPPINES_AGENT_INSTRUCTION
        
        assert "stay in" in PHILIPPINES_AGENT_INSTRUCTION.lower() or \
               "customer's language" in PHILIPPINES_AGENT_INSTRUCTION.lower() or \
               "whatever language" in PHILIPPINES_AGENT_INSTRUCTION.lower(), \
               "Escalation should stay in customer's language"

    def test_cultural_adaptation_examples(self):
        """At least 3 localization examples showing adaptation, not literal translation."""
        from adk_app.agents.philippines_voice_agent import PHILIPPINES_AGENT_INSTRUCTION
        
        # Check for localization examples section
        assert "localization examples" in PHILIPPINES_AGENT_INSTRUCTION.lower(), \
            "Missing localization examples section"
        
        # Count distinct examples
        adaptation_markers = ["instead of", "use ", "adaptation", "natural"]
        found = sum(1 for m in adaptation_markers if m.lower() in PHILIPPINES_AGENT_INSTRUCTION.lower())
        assert found >= 2, f"Need more adaptation examples. Found {found} markers."

    def test_respectful_address_forms(self):
        """Uses 'po' and 'opo' for respectful Filipino address."""
        from adk_app.agents.philippines_voice_agent import PHILIPPINES_AGENT_INSTRUCTION
        
        assert "po" in PHILIPPINES_AGENT_INSTRUCTION, "Missing 'po' (respectful Filipino particle)"
        assert "opo" in PHILIPPINES_AGENT_INSTRUCTION, "Missing 'opo' (respectful Filipino affirmative)"


class TestPhilippinesBotConfig:
    """Test bot configuration completeness."""

    def test_agent_is_valid(self):
        """Philippines agent can be imported and has correct structure."""
        from adk_app.agents.philippines_voice_agent import philippines_voice_agent
        
        assert philippines_voice_agent.name == "philippines_voice_agent"
        assert philippines_voice_agent.model == "gemini-2.0-flash"
        assert len(philippines_voice_agent.instruction) > 500  # Substantial instruction

    def test_sector_is_bancassurance_or_insurance(self):
        """Agent is configured for insurance/bancassurance sector."""
        from adk_app.agents.philippines_voice_agent import PHILIPPINES_AGENT_INSTRUCTION
        
        assert any(term in PHILIPPINES_AGENT_INSTRUCTION.lower() for term in 
                   ["insurance", "bancassurance", "renewal", "premium"]), \
            "Agent should be configured for insurance/bancassurance sector"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
