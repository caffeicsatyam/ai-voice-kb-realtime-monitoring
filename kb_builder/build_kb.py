"""
KB Build Orchestrator
Runs the full pipeline: ingest -> clean -> dedupe -> normalize -> PII -> chunk -> index.
"""
import json
import sys
from pathlib import Path

from kb_builder.ingest import ingest_source_docs
from kb_builder.clean import clean_records
from kb_builder.dedupe import deduplicate_records
from kb_builder.normalize import normalize_records
from kb_builder.pii import scan_records_for_pii
from kb_builder.chunk import chunk_records
from kb_builder.build_index import build_index


def build_kb(
    source_dir: str = "source_docs",
    output_dir: str = "knowledge_base",
    max_chunk_tokens: int = 300,
    dedupe_threshold: float = 0.40,
):
    """
    Run the full KB build pipeline.
    
    Args:
        source_dir: Path to source documents.
        output_dir: Path to output knowledge base.
        max_chunk_tokens: Maximum words per chunk.
        dedupe_threshold: Jaccard similarity threshold for deduplication.
    """
    print("=" * 60)
    print("Knowledge Base Build Pipeline")
    print("=" * 60)

    # Ensure output directory exists
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Step 1: Ingest
    print("\n--- Step 1: Ingestion ---")
    records = ingest_source_docs(source_dir)

    # Step 2: Clean
    print("\n--- Step 2: Cleaning ---")
    records = clean_records(records)

    # Step 3: Deduplicate
    print("\n--- Step 3: Deduplication ---")
    records = deduplicate_records(records, threshold=dedupe_threshold)

    # Step 4: Normalize
    print("\n--- Step 4: Normalization ---")
    records = normalize_records(records)

    # Step 5: PII Scan
    print("\n--- Step 5: PII Detection & Redaction ---")
    records = scan_records_for_pii(records, redact=True)

    # Save records
    records_path = out_path / "records.jsonl"
    with open(records_path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"\n[Save] Wrote {len(records)} records to {records_path}")

    # Step 6: Chunk
    print("\n--- Step 6: Chunking ---")
    chunks = chunk_records(records, max_tokens=max_chunk_tokens)

    # Save chunks
    chunks_path = out_path / "chunks.jsonl"
    with open(chunks_path, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    print(f"[Save] Wrote {len(chunks)} chunks to {chunks_path}")

    # Step 7: Build Index
    print("\n--- Step 7: Index Building ---")
    index_path = str(out_path / "bm25_index.json")
    index = build_index(chunks, index_path)

    # Summary
    print("\n" + "=" * 60)
    print("Build Complete!")
    print(f"  Records: {len(records)}")
    print(f"  Chunks:  {len(chunks)}")
    print(f"  Index:   {index_path}")
    pii_records = sum(1 for r in records if r.get("contains_pii"))
    print(f"  PII flagged records: {pii_records}")
    categories = set(r.get("category", "") for r in records)
    print(f"  Categories: {', '.join(sorted(categories))}")
    print("=" * 60)

    return records, chunks, index


if __name__ == "__main__":
    build_kb()

