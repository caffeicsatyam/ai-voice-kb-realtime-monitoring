"""
Citation Guard Callback
Ensures KB retrieval results are referenced in agent responses.
"""
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def log_citation_usage(tool_name: str, tool_args: dict, tool_result: str, evidence_dir: str = "evidence"):
    """
    Log KB retrieval tool calls for evidence tracking.
    Called after retrieve_kb tool execution.
    """
    log_dir = Path(evidence_dir) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "tool": tool_name,
        "query": tool_args.get("query", ""),
        "category_filter": tool_args.get("category", None),
    }
    
    try:
        result_data = json.loads(tool_result)
        entry["status"] = result_data.get("status", "unknown")
        entry["result_count"] = result_data.get("result_count", 0)
        if "evidence" in result_data:
            entry["chunks_returned"] = [
                {"chunk_id": e.get("chunk_id"), "title": e.get("title"), "score": e.get("score")}
                for e in result_data["evidence"][:5]
            ]
    except (json.JSONDecodeError, KeyError):
        entry["raw_result_length"] = len(tool_result)
    
    filepath = log_dir / "retrieval_calls.jsonl"
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    logger.info(f"[Citation] Logged KB retrieval: query='{entry['query']}', results={entry.get('result_count', 0)}")
