"""
ADK Tool: Human Escalation
Logs escalation requests when the agent cannot handle a situation.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


EVIDENCE_DIR = os.environ.get("EVIDENCE_DIR", "evidence")


def escalate_to_human(
    reason: str,
    customer_name: Optional[str] = None,
    phone: Optional[str] = None,
    conversation_summary: Optional[str] = None,
    urgency: str = "normal",
) -> str:
    """
    Escalate the conversation to a human agent.
    
    Call this tool when:
    - The customer explicitly asks to speak with a human or manager.
    - The conversation involves a topic outside the agent's knowledge.
    - The customer is frustrated and needs personal attention.
    - There is a compliance or safety concern.
    
    Args:
        reason: Clear reason for escalation.
        customer_name: Name of the customer if known.
        phone: Customer's phone number for callback.
        conversation_summary: Brief summary of the conversation so far.
        urgency: Urgency level (normal, high, urgent).
    
    Returns:
        Confirmation message that escalation has been logged.
    """
    escalation_id = f"ESC-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    escalation = {
        "escalation_id": escalation_id,
        "created_at": datetime.now().isoformat(),
        "reason": reason,
        "customer_name": customer_name,
        "phone": phone,
        "conversation_summary": conversation_summary,
        "urgency": urgency,
        "status": "pending",
        "source": "voice_agent",
    }
    
    # Save to log
    log_dir = Path(EVIDENCE_DIR) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    filepath = log_dir / "escalations.jsonl"
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(escalation, ensure_ascii=False) + "\n")
    
    return json.dumps({
        "status": "escalated",
        "message": f"Escalation {escalation_id} has been created. A human agent will contact the customer shortly.",
        "escalation_id": escalation_id,
        "urgency": urgency,
    })


if __name__ == "__main__":
    print(escalate_to_human(
        reason="Customer requested to speak with a manager",
        customer_name="Test User",
        conversation_summary="Customer inquired about loan but wants human assistance.",
        urgency="normal",
    ))
