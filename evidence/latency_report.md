# Latency Report

Generated: 2026-07-18T14:28:36.882012

## Component Latency (from pipeline logs)

| Stage | Count | Min (ms) | P50 (ms) | P95 (ms) | Max (ms) | Mean (ms) |
|---|---|---|---|---|---|---|
| end_to_end | 52 | 0.1 | 0.2 | 0.6 | 0.9 | 0.3 |
| nudge_emission | 52 | 0.0 | 0.0 | 0.1 | 0.1 | 0.0 |
| signal_detection | 203 | 0.1 | 0.1 | 1.0 | 3.9 | 0.3 |

## End-to-End Latency (per-chunk)

| Metric | Detection (ms) | Emission (ms) | Total (ms) |
|---|---|---|---|
| P50 | 0.1 | 0.0 | 0.2 |
| P95 | 0.5 | 0.1 | 0.8 |
| Mean | 0.2 | 0.0 | 0.3 |
| Count | 24 | 24 | 24 |

## Latency by Signal Type

| Signal Type | Count | P50 (ms) | P95 (ms) |
|---|---|---|---|
| callback_need | 2 | 0.3 | 0.3 |
| frustration | 4 | 0.2 | 0.2 |
| missed_cross_sell | 2 | 0.2 | 0.2 |
| missing_disclosure | 6 | 0.2 | 0.3 |
| noisy_segment | 6 | 0.6 | 0.9 |
| payment_difficulty | 4 | 0.3 | 0.6 |

## Notes

- All latency measurements are for local signal detection + nudge emission (no network or ASR latency).
- In production, add ASR processing time (~100-500ms) and network latency.
- Signal detection uses deterministic regex rules, so latency is consistent.
- Nudge emission includes confidence checks, cooldown, and deduplication logic.
