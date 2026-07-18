"""
ADK Tool: Lead Qualification
Evaluates preliminary eligibility based on collected customer profile.
"""
import json
from typing import Optional


# Business rules for qualification
RULES = {
    "min_business_age_months": 6,
    "standard_min_business_age_months": 12,
    "min_monthly_revenue_standard": 100000,
    "min_monthly_revenue_early": 50000,
    "max_loan_amount_standard": 5000000,
    "max_loan_amount_early": 500000,
    "min_loan_amount": 20000,
    "max_dti_ratio": 0.40,
    "min_age": 21,
    "max_age_at_maturity": 65,
}


def qualify_lead(
    business_name: Optional[str] = None,
    business_age_months: Optional[int] = None,
    monthly_revenue: Optional[float] = None,
    requested_amount: Optional[float] = None,
    location: Optional[str] = None,
    loan_purpose: Optional[str] = None,
    has_business_registration: Optional[bool] = None,
    has_bank_statements: Optional[bool] = None,
    has_government_id: Optional[bool] = None,
    has_collateral: Optional[bool] = None,
    preferred_callback_time: Optional[str] = None,
) -> str:
    """
    Evaluate preliminary loan eligibility based on collected customer information.
    
    Call this tool after collecting the customer's key qualification details
    to determine if they are likely eligible, what product fits, and what
    information is still missing.
    
    Args:
        business_name: Name of the business.
        business_age_months: How many months the business has been operating.
        monthly_revenue: Average monthly gross revenue in PHP.
        requested_amount: Desired loan amount in PHP.
        location: Business location/city.
        loan_purpose: Intended use of loan funds.
        has_business_registration: Whether the applicant has DTI/SEC registration.
        has_bank_statements: Whether 6-month bank statements are available.
        has_government_id: Whether valid government IDs are available.
        has_collateral: Whether collateral is available.
        preferred_callback_time: When the customer prefers a callback.
    
    Returns:
        JSON with eligibility assessment, recommended product, missing fields, and reasons.
    """
    issues = []
    missing_fields = []
    eligible_products = []
    
    # Check required fields
    if business_age_months is None:
        missing_fields.append("business_age_months")
    if monthly_revenue is None:
        missing_fields.append("monthly_revenue")
    if requested_amount is None:
        missing_fields.append("requested_amount")
    
    # Evaluate if we have enough info
    if business_age_months is not None:
        if business_age_months < RULES["min_business_age_months"]:
            issues.append(f"Business age ({business_age_months} months) is below minimum requirement of {RULES['min_business_age_months']} months.")
        elif business_age_months < RULES["standard_min_business_age_months"]:
            eligible_products.append("early_stage_business_loan")
        else:
            eligible_products.append("standard_business_loan")
            eligible_products.append("working_capital_line")
    
    if monthly_revenue is not None:
        if monthly_revenue < RULES["min_monthly_revenue_early"]:
            issues.append(f"Monthly revenue (PHP {monthly_revenue:,.0f}) is below minimum requirement of PHP {RULES['min_monthly_revenue_early']:,.0f}.")
        elif monthly_revenue < RULES["min_monthly_revenue_standard"]:
            if "standard_business_loan" in eligible_products:
                eligible_products.remove("standard_business_loan")
                if "early_stage_business_loan" not in eligible_products:
                    eligible_products.append("early_stage_business_loan")
    
    if requested_amount is not None:
        if requested_amount < RULES["min_loan_amount"]:
            issues.append(f"Requested amount (PHP {requested_amount:,.0f}) is below minimum of PHP {RULES['min_loan_amount']:,.0f}.")
        elif requested_amount > RULES["max_loan_amount_standard"]:
            issues.append(f"Requested amount (PHP {requested_amount:,.0f}) exceeds maximum of PHP {RULES['max_loan_amount_standard']:,.0f}.")
        elif requested_amount > RULES["max_loan_amount_early"]:
            # Can only qualify for standard
            if "early_stage_business_loan" in eligible_products and "standard_business_loan" not in eligible_products:
                issues.append(f"Requested amount (PHP {requested_amount:,.0f}) exceeds Early Stage maximum of PHP {RULES['max_loan_amount_early']:,.0f}. Standard loan requires 12+ months business age.")
    
    # Check document readiness
    missing_docs = []
    if has_business_registration is False:
        missing_docs.append("business_registration")
    if has_bank_statements is False:
        missing_docs.append("bank_statements")
    if has_government_id is False:
        missing_docs.append("government_id")
    
    if not has_collateral and requested_amount and requested_amount > 500000:
        issues.append("Unsecured loans are limited to PHP 500,000. Collateral may be needed for the requested amount.")
    
    # Determine overall status
    if issues:
        status = "needs_review"
        if any("below minimum" in i.lower() for i in issues):
            status = "likely_ineligible"
    elif missing_fields:
        status = "incomplete"
    else:
        status = "likely_eligible"
    
    result = {
        "status": status,
        "eligible_products": eligible_products,
        "issues": issues,
        "missing_fields": missing_fields,
        "missing_documents": missing_docs,
        "profile_summary": {
            "business_name": business_name,
            "business_age_months": business_age_months,
            "monthly_revenue": monthly_revenue,
            "requested_amount": requested_amount,
            "location": location,
            "loan_purpose": loan_purpose,
            "preferred_callback_time": preferred_callback_time,
        },
        "next_steps": [],
    }
    
    # Determine next steps
    if status == "incomplete":
        result["next_steps"].append(f"Collect missing information: {', '.join(missing_fields)}")
    if missing_docs:
        result["next_steps"].append(f"Applicant needs to prepare: {', '.join(missing_docs)}")
    if status == "likely_eligible":
        result["next_steps"].append("Schedule document submission and formal application review.")
    if status == "likely_ineligible":
        result["next_steps"].append("Explain disqualification reason and suggest alternatives if available.")
    if preferred_callback_time:
        result["next_steps"].append(f"Schedule callback for {preferred_callback_time}.")
    
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    result = qualify_lead(
        business_name="JC's Store",
        business_age_months=18,
        monthly_revenue=200000,
        requested_amount=800000,
        location="Makati City",
        has_collateral=False,
    )
    print(result)
