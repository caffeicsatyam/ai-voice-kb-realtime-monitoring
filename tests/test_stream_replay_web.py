"""Replay-to-dashboard bridge tests."""

import json

from realtime_nudges import stream_replay


def test_replay_web_mode_posts_transcript_and_nudge_events(monkeypatch):
    posted = []
    monkeypatch.setattr(
        stream_replay,
        "SAMPLE_TRANSCRIPTS",
        {
            "demo": [
                {
                    "time": "00:00:01",
                    "speaker": "customer",
                    "text": "This is so frustrating.",
                }
            ]
        },
    )
    monkeypatch.setattr(
        stream_replay,
        "detect_signals",
        lambda transcript_chunk, agent_or_customer: json.dumps({
            "signals": [
                {
                    "signal_type": "frustration",
                    "confidence": 0.9,
                    "evidence": ["frustrating"],
                }
            ]
        }),
    )
    monkeypatch.setattr(
        stream_replay,
        "emit_nudge",
        lambda **kwargs: json.dumps({
            "emitted": True,
            "signal": "frustration",
            "priority": "high",
            "confidence": 0.9,
            "nudge": "Customer appears frustrated. Slow down.",
        }),
    )
    monkeypatch.setattr(
        stream_replay,
        "_post_nudge_event",
        lambda payload, api_url=None: posted.append(payload) or True,
    )

    results = stream_replay.replay_transcript(
        "demo",
        speed_factor=999,
        output_mode="web",
        api_url="http://testserver/api/nudge-event",
    )

    assert results["chunks_processed"] == 1
    assert [event["event_type"] for event in posted] == ["transcript", "nudge"]
    assert posted[0]["chunk"] == "This is so frustrating."
    assert posted[1]["signal"] == "frustration"
    assert posted[1]["analysis"] == "Customer appears frustrated. Slow down."