"""
ADK Tool: Knowledge Base Retrieval
Searches the local BM25 index and returns cited chunks.
"""
import json
import os
import sys
from pathlib import Path
from typing import Optional

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from kb_builder.build_index import BM25Index


# Global index singleton
_index: Optional[BM25Index] = None


def _get_index() -> BM25Index:
    """Lazy-load the BM25 index."""
    global _index
    if _index is None:
        index_path = os.environ.get("KB_INDEX_PATH", "knowledge_base/bm25_index.json")
        if not Path(index_path).exists():
            raise FileNotFoundError(
                f"KB index not found at {index_path}. Run 'python -m kb_builder.build_kb' first."
            )
        _index = BM25Index.load(index_path)
    return _index


def retrieve_kb(query: str, category: Optional[str] = None, top_k: int = 5) -> str:
    """
    Search the knowledge base for information relevant to the query.
    
    Use this tool whenever a customer asks about loan products, eligibility,
    required documents, pricing, fees, objections, or any policy question.
    Do NOT make up answers — always check the knowledge base first.
    
    Args:
        query: The search query describing what information is needed.
        category: Optional category filter. One of: qualification, documentation,
                  pricing, product, faq, objection, form.
        top_k: Number of results to return (default 5).
    
    Returns:
        JSON string with retrieved evidence chunks including source citations.
        If no relevant results are found, returns a message saying so.
    """
    index = _get_index()
    
    filters = {}
    if category:
        filters["category"] = category
    
    results = index.search(query, top_k=top_k, filters=filters)
    
    if not results:
        return json.dumps({
            "status": "no_results",
            "message": "No relevant information found in the knowledge base for this query.",
            "query": query,
        })
    
    evidence = []
    for r in results:
        evidence.append({
            "chunk_id": r.get("chunk_id", ""),
            "title": r.get("title", ""),
            "content": r.get("content", ""),
            "source_ref": r.get("source_ref", ""),
            "category": r.get("category", ""),
            "score": r.get("score", 0),
            "version": r.get("version", ""),
            "contains_pii": r.get("contains_pii", False),
        })
    
    return json.dumps({
        "status": "found",
        "query": query,
        "result_count": len(evidence),
        "evidence": evidence,
    }, indent=2)


def reload_index():
    """Force reload of the KB index (useful after rebuilding)."""
    global _index
    _index = None
    _get_index()


if __name__ == "__main__":
    # Test search
    result = retrieve_kb("What documents do I need for a loan?")
    print(result)
