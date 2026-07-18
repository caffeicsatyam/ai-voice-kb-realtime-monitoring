"""
Latency Logger Callback
Measures and logs tool call execution times.
"""
import json
import time
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class LatencyTracker:
    """Tracks latency for pipeline stages."""
    
    def __init__(self):
        self.measurements = []
    
    def record(self, stage: str, duration_ms: float, metadata: dict = None):
        """Record a latency measurement."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "duration_ms": round(duration_ms, 2),
            "metadata": metadata or {},
        }
        self.measurements.append(entry)
        logger.debug(f"[Latency] {stage}: {duration_ms:.2f}ms")
    
    def save(self, evidence_dir: str = "evidence"):
        """Save all measurements to evidence/logs/latency.jsonl."""
        log_dir = Path(evidence_dir) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = log_dir / "latency.jsonl"
        with open(filepath, "a", encoding="utf-8") as f:
            for entry in self.measurements:
                f.write(json.dumps(entry) + "\n")
        
        logger.info(f"[Latency] Saved {len(self.measurements)} measurements to {filepath}")
    
    def get_stats(self, stage: str = None) -> dict:
        """Compute P50, P95 stats for a stage or all stages."""
        entries = self.measurements
        if stage:
            entries = [e for e in entries if e["stage"] == stage]
        
        if not entries:
            return {"count": 0, "p50_ms": 0, "p95_ms": 0, "mean_ms": 0}
        
        durations = sorted(e["duration_ms"] for e in entries)
        n = len(durations)
        
        return {
            "stage": stage or "all",
            "count": n,
            "min_ms": round(durations[0], 2),
            "p50_ms": round(durations[n // 2], 2),
            "p95_ms": round(durations[int(n * 0.95)], 2),
            "max_ms": round(durations[-1], 2),
            "mean_ms": round(sum(durations) / n, 2),
        }


# Global tracker
latency_tracker = LatencyTracker()


def log_tool_latency(tool_name: str, start_time: float, end_time: float):
    """Log latency for a tool call."""
    duration_ms = (end_time - start_time) * 1000
    latency_tracker.record(
        stage=f"tool_{tool_name}",
        duration_ms=duration_ms,
        metadata={"tool": tool_name},
    )
