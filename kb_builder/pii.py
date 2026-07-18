"""
KB PII Detection Module
Detects and flags records containing personally identifiable information.
"""
import re
from typing import Optional


# PII detection patterns
PII_PATTERNS = {
    "phone_number": [
        r"\+63\s?\d{3}\s?\d{3}\s?\d{4}",       # PH mobile
        r"\b\d{4}[-\s]?\d{3}[-\s]?\d{4}\b",     # generic phone
        r"\b1-800-[A-Z]{4}\b",                    # toll-free
    ],
    "email": [
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    ],
    "national_id": [
        r"\bTIN:\s*\d{3}-\d{3}-\d{3}-\d{3}\b",      # TIN
        r"\b\d{2}-\d{7}-\d{1}\b",                     # SSS
        r"\bBP-\d{4}-\d{5}\b",                        # Business permit
        r"\bDTI.*?:\s*\d{4}-\d{5}\b",                 # DTI reg
        r"\bQF-\d{4}-\d{5}\b",                        # Internal ref
    ],
    "bank_account": [
        r"\b\d{12}\b",                                # 12-digit account
        r"Account\s*(?:Number|No\.?):\s*\d{6,}",
    ],
    "person_name": [
        r"Full Name:\s*[A-Z][a-z]+\s+(?:[A-Z][a-z]+\s+)*[A-Z][a-z]+",
        r"Agent\s+[A-Z][a-z]+\s+[A-Z][a-z]+",
        r"—\s*[A-Z][a-z]+\s+[A-Z]\.",                 # Testimonial attribution
    ],
    "address": [
        r"\d+\s+[A-Z][a-z]+\s+(?:Avenue|Street|Road|Blvd|Drive),\s*(?:Brgy\.|Barangay)",
    ],
}

# Redaction replacement
REDACTION_MAP = {
    "phone_number": "[PHONE_REDACTED]",
    "email": "[EMAIL_REDACTED]",
    "national_id": "[ID_REDACTED]",
    "bank_account": "[ACCOUNT_REDACTED]",
    "person_name": "[NAME_REDACTED]",
    "address": "[ADDRESS_REDACTED]",
}


def detect_pii(text: str) -> list[dict]:
    """
    Detect PII in text and return list of findings.
    
    Returns:
        List of dicts with: pii_type, pattern_matched, start, end
    """
    findings = []
    for pii_type, patterns in PII_PATTERNS.items():
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                findings.append({
                    "pii_type": pii_type,
                    "matched_text": match.group()[:20] + "..." if len(match.group()) > 20 else match.group(),
                    "start": match.start(),
                    "end": match.end(),
                })
    return findings


def redact_pii(text: str) -> tuple[str, list[dict]]:
    """
    Detect and redact PII from text.
    
    Returns:
        (redacted_text, list_of_findings)
    """
    findings = []
    redacted = text

    for pii_type, patterns in PII_PATTERNS.items():
        replacement = REDACTION_MAP.get(pii_type, "[REDACTED]")
        for pattern in patterns:
            matches = list(re.finditer(pattern, redacted))
            for match in matches:
                findings.append({
                    "pii_type": pii_type,
                    "original_snippet": match.group()[:20] + "...",
                })
            redacted = re.sub(pattern, replacement, redacted)

    return redacted, findings


def scan_records_for_pii(records: list[dict], redact: bool = True) -> list[dict]:
    """
    Scan all records for PII, flag them, and optionally redact.
    
    Args:
        records: List of record dicts.
        redact: If True, redact PII in content. If False, only flag.
    
    Returns:
        Updated records with contains_pii flag set.
    """
    pii_count = 0

    for record in records:
        findings = detect_pii(record["content"])

        if findings:
            record["contains_pii"] = True
            record["pii_types_found"] = list(set(f["pii_type"] for f in findings))
            pii_count += 1

            if redact:
                record["content"], _ = redact_pii(record["content"])
        else:
            record["contains_pii"] = False

    print(f"[PII] Scanned {len(records)} records, found PII in {pii_count}")
    return records


if __name__ == "__main__":
    test = "Contact Juan Dela Cruz at +63 917 123 4567 or juan@example.com. TIN: 123-456-789-000"
    findings = detect_pii(test)
    print(f"Found {len(findings)} PII items:")
    for f in findings:
        print(f"  - {f['pii_type']}: {f['matched_text']}")
    
    redacted, _ = redact_pii(test)
    print(f"\nRedacted: {redacted}")
