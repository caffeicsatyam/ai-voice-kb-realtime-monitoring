"""
KB Deduplication Module
Detects and removes near-duplicate records using shingling + Jaccard similarity.
"""
import re
from typing import Optional


def _shingle(text: str, k: int = 3) -> set[str]:
    """Create k-word shingles from text."""
    words = re.findall(r"\w+", text.lower())
    if len(words) < k:
        return {" ".join(words)}
    return {" ".join(words[i:i + k]) for i in range(len(words) - k + 1)}


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def deduplicate_records(
    records: list[dict],
    threshold: float = 0.85,
    shingle_k: int = 3,
) -> list[dict]:
    """
    Remove near-duplicate records using Jaccard similarity on shingles.
    
    Args:
        records: List of record dicts with 'content' field.
        threshold: Jaccard threshold above which records are considered duplicates.
        shingle_k: Number of words per shingle.
    
    Returns:
        Deduplicated list, keeping the first occurrence.
    """
    if not records:
        return records

    # Compute shingles for each record
    shingles = [_shingle(r["content"], shingle_k) for r in records]

    keep = []
    removed = []
    kept_indices = set()

    for i, record in enumerate(records):
        is_dup = False
        for j in kept_indices:
            sim = jaccard_similarity(shingles[i], shingles[j])
            if sim >= threshold:
                removed.append({
                    "removed_id": record.get("record_id", f"idx_{i}"),
                    "duplicate_of": records[j].get("record_id", f"idx_{j}"),
                    "similarity": round(sim, 3),
                })
                is_dup = True
                break

        if not is_dup:
            keep.append(record)
            kept_indices.add(i)

    if removed:
        print(f"[Dedupe] Removed {len(removed)} duplicates (threshold={threshold}):")
        for r in removed:
            print(f"  - {r['removed_id']} is duplicate of {r['duplicate_of']} (sim={r['similarity']})")
    else:
        print(f"[Dedupe] No duplicates found among {len(records)} records.")

    print(f"[Dedupe] Kept {len(keep)} unique records.")
    return keep


if __name__ == "__main__":
    test_records = [
        {"record_id": "r1", "content": "The quick brown fox jumps over the lazy dog"},
        {"record_id": "r2", "content": "The quick brown fox leaps over the lazy dog"},
        {"record_id": "r3", "content": "Something completely different about loans"},
    ]
    result = deduplicate_records(test_records, threshold=0.5)
    print(f"Result: {[r['record_id'] for r in result]}")
