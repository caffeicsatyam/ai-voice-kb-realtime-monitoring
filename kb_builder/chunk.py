"""
KB Chunking Module
Splits records into retrieval-sized chunks suitable for BM25 indexing.
"""
import hashlib
import re


def generate_chunk_id(record_id: str, chunk_index: int) -> str:
    """Generate a deterministic chunk ID."""
    return f"{record_id}_chunk_{chunk_index:03d}"


def split_into_chunks(
    text: str,
    max_tokens: int = 300,
    overlap_tokens: int = 50,
) -> list[str]:
    """
    Split text into overlapping chunks based on token count (approximated by words).
    
    Respects paragraph and section boundaries where possible.
    """
    paragraphs = re.split(r"\n\n+", text.strip())
    chunks = []
    current_chunk_parts = []
    current_word_count = 0

    for para in paragraphs:
        para_words = len(para.split())

        # If single paragraph exceeds max, split by sentences
        if para_words > max_tokens:
            sentences = re.split(r"(?<=[.!?])\s+", para)
            for sentence in sentences:
                sent_words = len(sentence.split())
                if current_word_count + sent_words > max_tokens and current_chunk_parts:
                    chunks.append("\n\n".join(current_chunk_parts))
                    # Keep overlap
                    overlap_text = " ".join(current_chunk_parts[-1].split()[-overlap_tokens:])
                    current_chunk_parts = [overlap_text]
                    current_word_count = len(overlap_text.split())
                current_chunk_parts.append(sentence)
                current_word_count += sent_words
        elif current_word_count + para_words > max_tokens and current_chunk_parts:
            chunks.append("\n\n".join(current_chunk_parts))
            # Keep overlap
            overlap_text = " ".join(current_chunk_parts[-1].split()[-overlap_tokens:])
            current_chunk_parts = [overlap_text]
            current_word_count = len(overlap_text.split())
            current_chunk_parts.append(para)
            current_word_count += para_words
        else:
            current_chunk_parts.append(para)
            current_word_count += para_words

    # Last chunk
    if current_chunk_parts:
        chunks.append("\n\n".join(current_chunk_parts))

    return chunks


def chunk_records(records: list[dict], max_tokens: int = 300) -> list[dict]:
    """
    Split all records into retrieval-sized chunks.
    
    Args:
        records: List of record dicts with 'content' field.
        max_tokens: Maximum approximate word count per chunk.
    
    Returns:
        List of chunk dicts with: chunk_id, record_id, content, title, category,
        product, source_type, source_ref, chunk_index.
    """
    all_chunks = []

    for record in records:
        text_chunks = split_into_chunks(record["content"], max_tokens=max_tokens)

        for i, chunk_text in enumerate(text_chunks):
            chunk = {
                "chunk_id": generate_chunk_id(record["record_id"], i),
                "record_id": record["record_id"],
                "content": chunk_text.strip(),
                "title": record.get("title", ""),
                "category": record.get("category", ""),
                "product": record.get("product", ""),
                "source_type": record.get("source_type", ""),
                "source_ref": record.get("source_ref", ""),
                "chunk_index": i,
                "total_chunks": len(text_chunks),
                "contains_pii": record.get("contains_pii", False),
                "version": record.get("version", "1.0"),
                "effective_date": record.get("effective_date", ""),
            }
            all_chunks.append(chunk)

    print(f"[Chunk] Split {len(records)} records into {len(all_chunks)} chunks (max_tokens={max_tokens})")
    return all_chunks


if __name__ == "__main__":
    test_text = "First paragraph with some content. " * 50 + "\n\n" + "Second paragraph. " * 30
    chunks = split_into_chunks(test_text, max_tokens=100)
    print(f"Split into {len(chunks)} chunks")
    for i, c in enumerate(chunks):
        print(f"  Chunk {i}: {len(c.split())} words")
