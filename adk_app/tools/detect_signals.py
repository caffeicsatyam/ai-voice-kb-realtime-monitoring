"""
ADK Tool: Signal Detection
Detects actionable signals from transcript chunks using rule-based analysis.
"""
import json
import re
from typing import Optional


# Signal patterns - keyword/phrase based detection
SIGNAL_PATTERNS = {
    "missed_cross_sell": {
        "triggers": [
            r"(?:only|just)\s+(?:need|want)\s+(?:the|a)\s+loan",
            r"no\s+(?:thanks|thank\s+you).*(?:insurance|credit\s+card|savings)",
            r"not\s+interested\s+in\s+(?:anything\s+else|other)",
        ],
        "context_keywords": ["insurance", "credit card", "savings", "investment", "protection"],
        "description": "Customer may benefit from additional products but agent did not explore",
    },
    "missing_disclosure": {
        "triggers": [
            r"(?:final|approved|guaranteed|certain|definitely)",
            r"(?:no\s+(?:additional|hidden|other)\s+(?:fees|charges|costs))",
            r"(?:approved\s+(?:right\s+away|immediately|instantly))",
        ],
        "required_disclaimers": [
            "subject to document verification",
            "subject to final approval",
            "terms and conditions apply",
            "rates may vary",
        ],
        "description": "Agent may have made promises without required disclaimers",
    },
    "frustration": {
        "triggers": [
            r"(?:already\s+(?:told|said|explained|gave)\s+you)",
            r"(?:how\s+many\s+times)",
            r"(?:this\s+is\s+(?:ridiculous|frustrating|taking\s+too\s+long))",
            r"(?:waste\s+(?:of|my)\s+time)",
            r"(?:never\s+mind|forget\s+it|just\s+cancel)",
            r"(?:i(?:'m|\s+am)\s+(?:done|tired|frustrated|angry|upset))",
            r"(?:speak\s+(?:to|with)\s+(?:a\s+)?(?:manager|supervisor|someone\s+else))",
        ],
        "description": "Customer shows signs of rising frustration",
    },
    "payment_difficulty": {
        "triggers": [
            r"(?:can(?:'t|not)\s+(?:afford|pay|manage))",
            r"(?:too\s+(?:expensive|high|much))",
            r"(?:(?:lower|reduce|decrease)\s+(?:the\s+)?(?:payment|rate|amount))",
            r"(?:(?:struggling|difficulty|hard|tight)\s+(?:with\s+)?(?:money|finances|payments|budget))",
        ],
        "description": "Customer indicates financial difficulty or payment concerns",
    },
    "callback_need": {
        "triggers": [
            r"(?:call\s+(?:me\s+)?back)",
            r"(?:(?:busy|occupied|unavailable)\s+(?:right\s+)?now)",
            r"(?:(?:can|could)\s+(?:you\s+)?(?:call|contact|reach)\s+(?:me\s+)?(?:later|tomorrow|next\s+week))",
            r"(?:(?:need|want)\s+(?:to\s+)?(?:think|consider|discuss|check)(?:\s+(?:about\s+)?it)?(?:\s+(?:first|more))?)",
        ],
        "description": "Customer wants a callback or needs time to decide",
    },
    "noisy_segment": {
        "triggers": [
            r"(?:\[(?:inaudible|unclear|noise|static|crosstalk)\])",
            r"(?:(?:can(?:'t|not)|cannot)\s+(?:hear|understand)\s+you)",
            r"(?:(?:sorry|pardon)\s+(?:what|could\s+you\s+repeat))",
            r"(?:breaking\s+up|bad\s+(?:connection|signal|line))",
        ],
        "description": "Audio quality issues detected — suppress low-confidence nudges",
    },
}

# Confidence modifiers
CONFIDENCE_BASE = {
    "missed_cross_sell": 0.75,
    "missing_disclosure": 0.80,
    "frustration": 0.82,
    "payment_difficulty": 0.78,
    "callback_need": 0.85,
    "noisy_segment": 0.90,
}


def detect_signals(
    transcript_chunk: str,
    conversation_context: Optional[str] = None,
    agent_or_customer: str = "unknown",
) -> str:
    """
    Analyze a transcript chunk for actionable signals.
    
    This tool detects important signals in call audio transcripts including
    missed cross-sell opportunities, compliance gaps, customer frustration,
    payment difficulties, and callback needs.
    
    Args:
        transcript_chunk: The text of the current transcript segment to analyze.
        conversation_context: Optional broader conversation context for better detection.
        agent_or_customer: Who is speaking: "agent", "customer", or "unknown".
    
    Returns:
        JSON with list of detected signals, each with type, confidence, and evidence.
    """
    signals = []
    text_lower = transcript_chunk.lower()
    full_context = (conversation_context or "") + " " + transcript_chunk
    
    for signal_type, config in SIGNAL_PATTERNS.items():
        matches = []
        
        for pattern in config["triggers"]:
            found = re.findall(pattern, text_lower)
            if found:
                matches.extend(found)
        
        if matches:
            # Calculate confidence
            base_confidence = CONFIDENCE_BASE.get(signal_type, 0.7)
            match_boost = min(len(matches) * 0.05, 0.15)
            confidence = min(base_confidence + match_boost, 0.99)
            
            # Check for context reinforcement
            if signal_type == "missing_disclosure" and "required_disclaimers" in config:
                # Check if any disclaimers were already given
                disclaimers_present = sum(
                    1 for d in config["required_disclaimers"]
                    if d.lower() in full_context.lower()
                )
                if disclaimers_present > 0:
                    confidence -= 0.15 * disclaimers_present
            
            # Skip noisy segment signals for agent speech
            if signal_type == "noisy_segment" and agent_or_customer == "agent":
                continue
            
            if confidence > 0.3:
                signals.append({
                    "signal_type": signal_type,
                    "confidence": round(confidence, 2),
                    "evidence": matches[:3],  # Keep top 3 matches
                    "description": config["description"],
                    "speaker": agent_or_customer,
                })
    
    return json.dumps({
        "chunk_analyzed": transcript_chunk[:100] + "..." if len(transcript_chunk) > 100 else transcript_chunk,
        "signals_detected": len(signals),
        "signals": signals,
    }, indent=2)


if __name__ == "__main__":
    # Test with a frustration signal
    test = "I already told you my business details three times! This is so frustrating."
    print(detect_signals(test, agent_or_customer="customer"))
    
    print("\n---\n")
    
    # Test with a disclosure issue
    test2 = "Yes, your loan is definitely approved! No additional fees at all."
    print(detect_signals(test2, agent_or_customer="agent"))
