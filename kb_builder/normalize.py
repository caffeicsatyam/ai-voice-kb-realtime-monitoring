"""
KB Normalization Module
Normalizes terminology, categories, dates, and field values.
"""
import re

# Synonym map: variant -> canonical term
TERM_SYNONYMS = {
    "requested funding": "requested loan amount",
    "principal": "loan amount",
    "loan principal": "loan amount",
    "funding amount": "loan amount",
    "credit amount": "loan amount",
    "monthly income": "monthly revenue",
    "gross income": "monthly revenue",
    "business revenue": "monthly revenue",
    "monthly sales": "monthly revenue",
    "operating period": "business age",
    "years in operation": "business age",
    "business duration": "business age",
    "time in business": "business age",
    "guaranty": "collateral",
    "security": "collateral",
    "pledge": "collateral",
    "amortization": "monthly repayment",
    "installment": "monthly repayment",
    "monthly payment": "monthly repayment",
}

# Category normalization
CATEGORY_NORMALIZE = {
    "product_info": "product",
    "product_overview": "product",
    "products": "product",
    "policy": "qualification",
    "eligibility": "qualification",
    "requirements": "qualification",
    "docs": "documentation",
    "documents": "documentation",
    "document_requirements": "documentation",
    "fees": "pricing",
    "rates": "pricing",
    "interest": "pricing",
    "costs": "pricing",
    "questions": "faq",
    "faqs": "faq",
    "frequently_asked": "faq",
    "objections": "objection",
    "handling": "objection",
    "complaints": "objection",
    "application_form": "form",
    "intake": "form",
}


def normalize_terms(text: str) -> str:
    """Replace synonym variants with canonical terms."""
    normalized = text
    for variant, canonical in TERM_SYNONYMS.items():
        pattern = re.compile(re.escape(variant), re.IGNORECASE)
        normalized = pattern.sub(canonical, normalized)
    return normalized


def normalize_category(category: str) -> str:
    """Normalize category names to canonical values."""
    clean = category.lower().strip()
    return CATEGORY_NORMALIZE.get(clean, clean)


def normalize_records(records: list[dict]) -> list[dict]:
    """Apply normalization to all records."""
    normalized = []
    term_changes = 0

    for record in records:
        r = dict(record)

        # Normalize content terms
        original = r["content"]
        r["content"] = normalize_terms(r["content"])
        if r["content"] != original:
            term_changes += 1

        # Normalize title terms
        r["title"] = normalize_terms(r["title"])

        # Normalize category
        r["category"] = normalize_category(r["category"])

        normalized.append(r)

    print(f"[Normalize] Processed {len(records)} records, normalized terms in {term_changes}")
    return normalized


if __name__ == "__main__":
    test = "The requested funding amount and monthly income determine your eligibility."
    print(f"Before: {test}")
    print(f"After:  {normalize_terms(test)}")
