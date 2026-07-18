"""
KB Ingestion Module
Reads source documents from source_docs/ and extracts structured records.
"""
import os
import re
import hashlib
from pathlib import Path
from typing import Optional


# Map directory names to source types and categories
SOURCE_TYPE_MAP = {
    "policy_docs": "policy_doc",
    "web_pages": "web_page",
    "faq_docs": "faq_doc",
    "forms": "form",
    "multilingual": "multilingual_doc",
}

CATEGORY_MAP = {
    "eligibility": "qualification",
    "required_documents": "documentation",
    "pricing_fees": "pricing",
    "product_overview": "product",
    "product_overview_duplicate": "product",
    "loan_faq": "faq",
    "objection_handling": "objection",
    "intake_form_sample": "form",
}


def generate_record_id(source_ref: str, section_title: str) -> str:
    """Generate a deterministic record ID from source reference and section."""
    hash_input = f"{source_ref}:{section_title}"
    short_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
    return f"kb_{short_hash}"


def extract_sections(content: str, source_path: str) -> list[dict]:
    """Split a markdown document into section-level records."""
    sections = []
    current_title = ""
    current_content_lines = []
    current_level = 0

    lines = content.split("\n")

    for line in lines:
        heading_match = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading_match:
            # Save previous section
            if current_content_lines:
                section_text = "\n".join(current_content_lines).strip()
                if section_text and len(section_text) > 20:
                    sections.append({
                        "title": current_title,
                        "content": section_text,
                        "heading_level": current_level,
                    })
            current_level = len(heading_match.group(1))
            current_title = heading_match.group(2).strip()
            current_content_lines = []
        else:
            current_content_lines.append(line)

    # Last section
    if current_content_lines:
        section_text = "\n".join(current_content_lines).strip()
        if section_text and len(section_text) > 20:
            sections.append({
                "title": current_title,
                "content": section_text,
                "heading_level": current_level,
            })

    return sections


def ingest_source_docs(source_dir: str = "source_docs") -> list[dict]:
    """
    Read all markdown files from source_docs/ and produce raw records.
    
    Returns a list of record dicts with:
    - record_id, title, content, category, product, source_type, source_ref, version
    """
    records = []
    source_path = Path(source_dir)

    if not source_path.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    for subdir in sorted(source_path.iterdir()):
        if not subdir.is_dir():
            continue

        source_type = SOURCE_TYPE_MAP.get(subdir.name, "unknown")

        for filepath in sorted(subdir.glob("*.md")):
            content = filepath.read_text(encoding="utf-8")
            file_stem = filepath.stem
            category = CATEGORY_MAP.get(file_stem, "general")
            source_ref = str(filepath.as_posix())

            # Extract sections
            sections = extract_sections(content, source_ref)

            if not sections:
                # Treat entire file as one record
                record_id = generate_record_id(source_ref, file_stem)
                records.append({
                    "record_id": record_id,
                    "title": file_stem.replace("_", " ").title(),
                    "content": content.strip(),
                    "category": category,
                    "product": "small_business_loan",
                    "source_type": source_type,
                    "source_ref": source_ref,
                    "version": "1.0",
                    "contains_pii": False,
                    "effective_date": "2026-07-18",
                })
            else:
                for section in sections:
                    section_anchor = section["title"].lower().replace(" ", "-")
                    section_anchor = re.sub(r"[^a-z0-9\-]", "", section_anchor)
                    ref = f"{source_ref}#{section_anchor}"
                    record_id = generate_record_id(source_ref, section["title"])

                    records.append({
                        "record_id": record_id,
                        "title": section["title"],
                        "content": section["content"],
                        "category": category,
                        "product": "small_business_loan",
                        "source_type": source_type,
                        "source_ref": ref,
                        "version": "1.0",
                        "contains_pii": False,
                        "effective_date": "2026-07-18",
                    })

    print(f"[Ingest] Extracted {len(records)} raw records from {source_dir}/")
    return records


if __name__ == "__main__":
    records = ingest_source_docs()
    for r in records[:3]:
        print(f"  {r['record_id']}: {r['title']} ({r['category']})")
