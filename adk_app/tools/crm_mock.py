"""
ADK Tool: Mock CRM Actions
Creates local JSON records for lead creation and callback scheduling.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


EVIDENCE_DIR = os.environ.get("EVIDENCE_DIR", "evidence")


def _ensure_log_dir():
    """Ensure evidence/logs directory exists."""
    log_dir = Path(EVIDENCE_DIR) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def _append_log(filename: str, entry: dict):
    """Append a JSON entry to a log file."""
    log_dir = _ensure_log_dir()
    filepath = log_dir / filename
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def create_mock_crm_lead(
    business_name: str,
    contact_name: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    business_age_months: Optional[int] = None,
    monthly_revenue: Optional[float] = None,
    requested_amount: Optional[float] = None,
    location: Optional[str] = None,
    loan_purpose: Optional[str] = None,
    eligibility_status: Optional[str] = None,
    notes: Optional[str] = None,
) -> str:
    """
    Create a mock CRM lead record and save it locally.
    
    Call this tool after qualifying a customer to record their information
    as a lead in the CRM system.
    
    Args:
        business_name: Name of the business.
        contact_name: Name of the contact person.
        phone: Contact phone number.
        email: Contact email.
        business_age_months: Months in operation.
        monthly_revenue: Monthly gross revenue in PHP.
        requested_amount: Desired loan amount in PHP.
        location: Business location.
        loan_purpose: Purpose of the loan.
        eligibility_status: Current eligibility assessment.
        notes: Additional notes from the conversation.
    
    Returns:
        Confirmation message with the created lead ID.
    """
    lead_id = f"LEAD-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    lead = {
        "lead_id": lead_id,
        "created_at": datetime.now().isoformat(),
        "business_name": business_name,
        "contact_name": contact_name,
        "phone": phone,
        "email": email,
        "business_age_months": business_age_months,
        "monthly_revenue": monthly_revenue,
        "requested_amount": requested_amount,
        "location": location,
        "loan_purpose": loan_purpose,
        "eligibility_status": eligibility_status,
        "notes": notes,
        "status": "new",
        "source": "voice_agent",
    }
    
    _append_log("crm_leads.jsonl", lead)
    
    return json.dumps({
        "status": "success",
        "message": f"Lead {lead_id} created successfully in CRM.",
        "lead_id": lead_id,
    })


def schedule_callback(
    contact_name: str,
    phone: Optional[str] = None,
    preferred_time: Optional[str] = None,
    reason: Optional[str] = None,
    priority: str = "normal",
) -> str:
    """
    Schedule a callback for the customer.
    
    Call this tool when a customer requests a callback or when the agent
    needs to schedule a follow-up for document collection or further discussion.
    
    Args:
        contact_name: Name of the person to call back.
        phone: Contact phone number.
        preferred_time: Customer's preferred callback time.
        reason: Reason for the callback.
        priority: Priority level (normal, high, urgent).
    
    Returns:
        Confirmation message with callback reference.
    """
    callback_id = f"CB-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    callback = {
        "callback_id": callback_id,
        "created_at": datetime.now().isoformat(),
        "contact_name": contact_name,
        "phone": phone,
        "preferred_time": preferred_time,
        "reason": reason,
        "priority": priority,
        "status": "scheduled",
        "source": "voice_agent",
    }
    
    _append_log("callbacks.jsonl", callback)
    
    return json.dumps({
        "status": "success",
        "message": f"Callback {callback_id} scheduled successfully.",
        "callback_id": callback_id,
        "preferred_time": preferred_time,
    })


if __name__ == "__main__":
    print(create_mock_crm_lead(
        business_name="Test Business",
        contact_name="Test User",
        monthly_revenue=200000,
        requested_amount=500000,
    ))
    print(schedule_callback(
        contact_name="Test User",
        preferred_time="Tomorrow 2PM",
        reason="Document collection follow-up",
    ))
