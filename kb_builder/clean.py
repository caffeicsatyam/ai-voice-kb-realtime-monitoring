"""
KB Cleaning Module
Removes navigation, headers, footers, boilerplate, and normalizes content.
"""
import re


# Patterns for web page noise
NOISE_PATTERNS = [
    r"<!--\s*Navigation:.*?-->",
    r"<!--\s*Header:.*?-->",
    r"<!--\s*Footer:.*?-->",
    r"<!--\s*Contact:.*?-->",
    r"<!--.*?-->",
    r"\*FOR INTERNAL USE ONLY\*.*$",
]

# Boilerplate phrases to remove
BOILERPLATE_PHRASES = [
    "Click here to learn more",
    "Subscribe to our newsletter",
    "Follow us on social media",
    "All rights reserved",
    "Terms and conditions apply",
]


def clean_content(text: str) -> str:
    """Remove noise, boilerplate, and normalize whitespace."""
    cleaned = text

    # Remove HTML comments (navigation, headers, footers)
    for pattern in NOISE_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL | re.MULTILINE)

    # Remove boilerplate phrases
    for phrase in BOILERPLATE_PHRASES:
        cleaned = cleaned.replace(phrase, "")

    # Normalize whitespace
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    cleaned = cleaned.strip()

    return cleaned


def clean_records(records: list[dict]) -> list[dict]:
    """Clean content for all records."""
    cleaned = []
    noise_removed_count = 0

    for record in records:
        original_len = len(record["content"])
        clean_text = clean_content(record["content"])

        if len(clean_text) < original_len:
            noise_removed_count += 1

        if len(clean_text) > 10:  # Skip empty records after cleaning
            record["content"] = clean_text
            cleaned.append(record)

    print(f"[Clean] Processed {len(records)} records, removed noise from {noise_removed_count}, kept {len(cleaned)}")
    return cleaned


if __name__ == "__main__":
    test = "<!-- Navigation: Home | About -->\n# Test\nReal content here.\n<!-- Footer: Copyright 2024 -->"
    print(clean_content(test))
