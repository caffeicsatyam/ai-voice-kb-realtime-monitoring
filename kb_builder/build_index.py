"""
KB Index Builder
Builds a BM25 index over chunks for keyword-based retrieval.
"""
import json
import math
import re
from pathlib import Path
from typing import Optional


class BM25Index:
    """Simple BM25 index for local retrieval."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus = []       # list of tokenized documents
        self.doc_lens = []     # document lengths
        self.avg_dl = 0.0      # average document length
        self.idf = {}          # inverse document frequency
        self.doc_count = 0
        self.chunks = []       # original chunk dicts

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization: lowercase, split on non-alphanumeric."""
        stop_words = {
            "a", "an", "and", "are", "as", "at", "be", "by", "do", "for", "from",
            "has", "have", "how", "i", "in", "is", "it", "my", "of", "on", "or",
            "that", "the", "this", "to", "was", "we", "what", "when", "with", "you",
            "your",
        }
        return [token for token in re.findall(r"\w+", text.lower()) if token not in stop_words]

    def fit(self, chunks: list[dict]):
        """Build the BM25 index from chunks."""
        self.chunks = chunks
        self.corpus = []
        self.doc_lens = []

        # Tokenize all documents
        for chunk in chunks:
            tokens = self._tokenize(chunk["content"])
            self.corpus.append(tokens)
            self.doc_lens.append(len(tokens))

        self.doc_count = len(self.corpus)
        self.avg_dl = sum(self.doc_lens) / self.doc_count if self.doc_count > 0 else 0

        # Compute IDF
        df = {}  # document frequency
        for doc_tokens in self.corpus:
            seen = set(doc_tokens)
            for token in seen:
                df[token] = df.get(token, 0) + 1

        self.idf = {}
        for token, freq in df.items():
            self.idf[token] = math.log(
                (self.doc_count - freq + 0.5) / (freq + 0.5) + 1
            )

        print(f"[Index] Built BM25 index: {self.doc_count} documents, {len(self.idf)} terms")

    def search(self, query: str, top_k: int = 5, filters: Optional[dict] = None) -> list[dict]:
        """
        Search the index with a query.
        
        Args:
            query: Search query string.
            top_k: Number of top results to return.
            filters: Optional dict of field:value filters (e.g., {"category": "pricing"}).
        
        Returns:
            List of result dicts with chunk data plus 'score'.
        """
        query_tokens = self._tokenize(query)
        scores = []

        for i, doc_tokens in enumerate(self.corpus):
            # Apply filters
            if filters:
                chunk = self.chunks[i]
                skip = False
                for key, value in filters.items():
                    if chunk.get(key) != value:
                        skip = True
                        break
                if skip:
                    continue

            score = 0.0
            dl = self.doc_lens[i]

            # Count term frequencies in document
            tf_map = {}
            for token in doc_tokens:
                tf_map[token] = tf_map.get(token, 0) + 1

            for qtoken in query_tokens:
                if qtoken not in self.idf:
                    continue
                tf = tf_map.get(qtoken, 0)
                idf = self.idf[qtoken]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * dl / self.avg_dl)
                score += idf * numerator / denominator

            # Headings carry meaningful business intent in the source material.
            # A small title match boost prevents generic body text from outranking
            # the record that directly answers a question such as an objection.
            title_tokens = set(self._tokenize(self.chunks[i].get("title", "")))
            title_matches = sum(1 for token in query_tokens if len(token) > 2 and token in title_tokens)
            score += title_matches * 1.2

            scores.append((i, score))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in scores[:top_k]:
            if score <= 0:
                continue
            result = dict(self.chunks[idx])
            result["score"] = round(score, 4)
            results.append(result)

        return results

    def save(self, path: str):
        """Save index state to JSON."""
        state = {
            "k1": self.k1,
            "b": self.b,
            "doc_count": self.doc_count,
            "avg_dl": self.avg_dl,
            "idf": self.idf,
            "corpus": self.corpus,
            "doc_lens": self.doc_lens,
            "chunks": self.chunks,
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        print(f"[Index] Saved index to {path}")

    @classmethod
    def load(cls, path: str) -> "BM25Index":
        """Load index from JSON."""
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)

        idx = cls(k1=state["k1"], b=state["b"])
        idx.doc_count = state["doc_count"]
        idx.avg_dl = state["avg_dl"]
        idx.idf = state["idf"]
        idx.corpus = state["corpus"]
        idx.doc_lens = state["doc_lens"]
        idx.chunks = state["chunks"]
        return idx


def build_index(chunks: list[dict], index_path: str = "knowledge_base/bm25_index.json") -> BM25Index:
    """Build and save a BM25 index from chunks."""
    index = BM25Index()
    index.fit(chunks)
    index.save(index_path)
    return index


if __name__ == "__main__":
    test_chunks = [
        {"chunk_id": "c1", "content": "Business loan eligibility requires 12 months of operation"},
        {"chunk_id": "c2", "content": "Interest rates range from 1.2 to 2.5 percent per month"},
        {"chunk_id": "c3", "content": "Required documents include bank statements and business registration"},
    ]
    idx = build_index(test_chunks, "knowledge_base/bm25_index.json")
    results = idx.search("what documents do I need")
    for r in results:
        print(f"  {r['chunk_id']}: score={r['score']}")






