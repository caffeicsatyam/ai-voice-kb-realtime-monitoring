"""
Latency Report Generator
Computes and formats P50/P95 latency metrics from replay results.
"""
import json
import sys
from pathlib import Path
from datetime import datetime


def compute_percentile(values: list, percentile: float) -> float:
    """Compute a percentile from a sorted list."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    index = int(len(sorted_vals) * percentile / 100)
    index = min(index, len(sorted_vals) - 1)
    return sorted_vals[index]


def generate_latency_report(evidence_dir: str = "evidence") -> str:
    """
    Generate a formatted latency report from evidence/logs/ data.
    
    Returns:
        Markdown-formatted report string.
    """
    log_dir = Path(evidence_dir) / "logs"
    
    # Collect all replay results
    all_measurements = []
    for f in log_dir.glob("replay_*.json"):
        with open(f, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            all_measurements.extend(data.get("latency_measurements", []))
    
    # Collect latency.jsonl entries
    latency_file = log_dir / "latency.jsonl"
    stage_data = {}
    if latency_file.exists():
        with open(latency_file, "r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    entry = json.loads(line)
                    stage = entry.get("stage", "unknown")
                    if stage not in stage_data:
                        stage_data[stage] = []
                    stage_data[stage].append(entry["duration_ms"])
    
    # Build report
    report = "# Latency Report\n\n"
    report += f"Generated: {datetime.now().isoformat()}\n\n"
    
    # Component latency from JSONL
    if stage_data:
        report += "## Component Latency (from pipeline logs)\n\n"
        report += "| Stage | Count | Min (ms) | P50 (ms) | P95 (ms) | Max (ms) | Mean (ms) |\n"
        report += "|---|---|---|---|---|---|---|\n"
        
        for stage, values in sorted(stage_data.items()):
            n = len(values)
            sorted_v = sorted(values)
            p50 = compute_percentile(values, 50)
            p95 = compute_percentile(values, 95)
            mean = sum(values) / n
            report += f"| {stage} | {n} | {sorted_v[0]:.1f} | {p50:.1f} | {p95:.1f} | {sorted_v[-1]:.1f} | {mean:.1f} |\n"
        report += "\n"
    
    # End-to-end from replay results
    if all_measurements:
        report += "## End-to-End Latency (per-chunk)\n\n"
        
        detection_times = [m["detection_ms"] for m in all_measurements]
        emission_times = [m["emission_ms"] for m in all_measurements]
        total_times = [m["total_ms"] for m in all_measurements]
        
        report += "| Metric | Detection (ms) | Emission (ms) | Total (ms) |\n"
        report += "|---|---|---|---|\n"
        report += f"| P50 | {compute_percentile(detection_times, 50):.1f} | {compute_percentile(emission_times, 50):.1f} | {compute_percentile(total_times, 50):.1f} |\n"
        report += f"| P95 | {compute_percentile(detection_times, 95):.1f} | {compute_percentile(emission_times, 95):.1f} | {compute_percentile(total_times, 95):.1f} |\n"
        report += f"| Mean | {sum(detection_times)/len(detection_times):.1f} | {sum(emission_times)/len(emission_times):.1f} | {sum(total_times)/len(total_times):.1f} |\n"
        report += f"| Count | {len(detection_times)} | {len(emission_times)} | {len(total_times)} |\n"
        report += "\n"
        
        # By signal type
        signal_types = set(m["signal_type"] for m in all_measurements)
        if signal_types:
            report += "## Latency by Signal Type\n\n"
            report += "| Signal Type | Count | P50 (ms) | P95 (ms) |\n"
            report += "|---|---|---|---|\n"
            for sig in sorted(signal_types):
                sig_times = [m["total_ms"] for m in all_measurements if m["signal_type"] == sig]
                report += f"| {sig} | {len(sig_times)} | {compute_percentile(sig_times, 50):.1f} | {compute_percentile(sig_times, 95):.1f} |\n"
            report += "\n"
    
    report += "## Notes\n\n"
    report += "- All latency measurements are for local signal detection + nudge emission (no network or ASR latency).\n"
    report += "- In production, add ASR processing time (~100-500ms) and network latency.\n"
    report += "- Signal detection uses deterministic regex rules, so latency is consistent.\n"
    report += "- Nudge emission includes confidence checks, cooldown, and deduplication logic.\n"
    
    return report


def save_report(evidence_dir: str = "evidence"):
    """Generate and save the latency report."""
    report = generate_latency_report(evidence_dir)
    
    output_path = Path(evidence_dir) / "latency_report.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Latency report saved to {output_path}")
    
    return report


if __name__ == "__main__":
    report = save_report()
    print(report)
