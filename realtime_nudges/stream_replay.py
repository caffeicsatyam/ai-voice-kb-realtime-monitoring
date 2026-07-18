"""
Real-Time Stream Replay
Replays pre-recorded transcripts at simulated real-time speed,
sending chunks to the nudge pipeline and measuring latency.
"""
import json
import time
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from adk_app.tools.detect_signals import detect_signals
from adk_app.tools.emit_nudge import emit_nudge, reset_nudge_state
from adk_app.callbacks.latency_logger import latency_tracker


# Sample call transcripts for demo replay
SAMPLE_TRANSCRIPTS = {
    "cooperative": [
        {"time": "00:00:02", "speaker": "agent", "text": "Good morning! Thank you for calling QuickFund Lending. My name is Maya, and I'll be helping you today with our business loan products. May I know who I'm speaking with?"},
        {"time": "00:00:10", "speaker": "customer", "text": "Hi Maya, this is Carlos. I own a small restaurant in Makati and I'm looking for a loan to expand."},
        {"time": "00:00:18", "speaker": "agent", "text": "Great to hear from you, Carlos! A restaurant expansion sounds exciting. Let me ask you a few questions to see which loan product would be best for you. How long has your restaurant been operating?"},
        {"time": "00:00:28", "speaker": "customer", "text": "We've been open for about two years now. Business has been good, averaging around 350,000 pesos a month in revenue."},
        {"time": "00:00:36", "speaker": "agent", "text": "That's wonderful! Two years of operation and PHP 350,000 monthly revenue puts you in a good position. How much are you looking to borrow for the expansion?"},
        {"time": "00:00:45", "speaker": "customer", "text": "I'm thinking around 1.5 million pesos. I want to renovate the dining area and add a small catering kitchen."},
        {"time": "00:00:55", "speaker": "agent", "text": "A PHP 1.5 million loan for renovation and kitchen expansion. Do you have any collateral available, like property or equipment? For amounts above 500,000, having collateral can get you a better interest rate."},
        {"time": "00:01:05", "speaker": "customer", "text": "I own the commercial unit where the restaurant is located. Would that work?"},
        {"time": "00:01:12", "speaker": "agent", "text": "Yes, real property is one of our accepted collateral types. That should qualify you for our secured loan rate. Do you have your business registration, bank statements for the last 6 months, and government ID ready?"},
        {"time": "00:01:24", "speaker": "customer", "text": "Yes, I have all of those. When can I submit the application?"},
        {"time": "00:01:30", "speaker": "agent", "text": "You can submit online or visit any of our partner branches. The approval process typically takes 5-7 business days. Based on what you've told me, you look like a strong candidate. Shall I create a preliminary application for you?"},
    ],
    "objection_with_missed_cross_sell": [
        {"time": "00:00:02", "speaker": "agent", "text": "Good afternoon! This is Maya from QuickFund. How can I help you today?"},
        {"time": "00:00:08", "speaker": "customer", "text": "Hi, I want to ask about a business loan. But first, your interest rates seem too high compared to banks."},
        {"time": "00:00:16", "speaker": "agent", "text": "I understand your concern about the interest rate. Our rates do reflect the speed and flexibility we offer. While banks may quote lower rates, they typically require 3 or more years of business history and take 4 to 8 weeks for approval. We can approve qualified applicants in just 5 to 7 business days."},
        {"time": "00:00:30", "speaker": "customer", "text": "I see. Well my business is only 10 months old, so banks won't work for me anyway. I just need the loan, nothing else."},
        {"time": "00:00:40", "speaker": "agent", "text": "With 10 months of operation, you'd qualify for our Early Stage Business Loan with amounts up to PHP 500,000. Your loan is definitely approved once we process your documents. No additional fees at all."},
        {"time": "00:00:52", "speaker": "customer", "text": "Wait, are you sure it's guaranteed? That sounds too good to be true."},
        {"time": "00:01:00", "speaker": "agent", "text": "Well, I mean we have a high approval rate for applicants who meet our criteria. Let me check  final approval does depend on the complete document review. I apologize for the confusion."},
        {"time": "00:01:12", "speaker": "customer", "text": "Okay. What documents do I need? And why do you need my bank statements?"},
        {"time": "00:01:20", "speaker": "agent", "text": "For the Early Stage loan, you'll need your DTI or SEC registration, current business permit, two government IDs, 6 months of bank statements, and a simple one-page business plan. Bank statements help us verify your actual cash flow and determine the right loan amount for your situation."},
    ],
    "frustration_call": [
        {"time": "00:00:02", "speaker": "agent", "text": "Good morning! This is QuickFund Lending. How may I assist you today?"},
        {"time": "00:00:08", "speaker": "customer", "text": "Yes, I called yesterday about my loan application and the person I spoke to asked me the same questions. Now I have to repeat everything again?"},
        {"time": "00:00:18", "speaker": "agent", "text": "I apologize for the inconvenience. Could you please give me your reference number so I can pull up your file?"},
        {"time": "00:00:24", "speaker": "customer", "text": "I already told you my details yesterday! This is so frustrating. How many times do I need to explain my situation?"},
        {"time": "00:00:32", "speaker": "agent", "text": "I completely understand your frustration and I sincerely apologize. Let me check our system. Can you tell me your business name?"},
        {"time": "00:00:40", "speaker": "customer", "text": "It's Pedro's Auto Repair. I already gave my bank statements and business registration. Your colleague said I'd hear back in 2 days and it's been a week!"},
        {"time": "00:00:52", "speaker": "agent", "text": "I'm sorry about the delay, Mr. Pedro. Let me look into this right away. I can see your application in our system. It appears there was a question about one of your bank statements."},
        {"time": "00:01:02", "speaker": "customer", "text": "This is ridiculous. I'm done explaining things. I want to talk to a manager. This is a waste of my time."},
        {"time": "00:01:10", "speaker": "agent", "text": "Of course. Let me connect you with a senior loan specialist right away. I'll make sure they have all the context so you don't need to repeat yourself. May I have a good callback number?"},
    ],
    "noisy_call": [
        {"time": "00:00:02", "speaker": "agent", "text": "Hello! Thank you for calling QuickFund. How can I help you?"},
        {"time": "00:00:06", "speaker": "customer", "text": "[inaudible] ...business loan... [static] ...want to know about..."},
        {"time": "00:00:14", "speaker": "agent", "text": "I'm sorry, I'm having trouble hearing you. Could you please repeat that?"},
        {"time": "00:00:20", "speaker": "customer", "text": "[unclear] ...can't hear you either... bad connection... [noise]"},
        {"time": "00:00:28", "speaker": "agent", "text": "It seems we have a bad connection. Could you try calling back from a different location, or shall I call you back?"},
        {"time": "00:00:36", "speaker": "customer", "text": "Breaking up... call me back later... [inaudible]"},
        {"time": "00:00:42", "speaker": "agent", "text": "Sure, I'll schedule a callback. What time works best for you tomorrow?"},
    ],
}


def replay_transcript(
    transcript_name: str = "cooperative",
    speed_factor: float = 1.0,
    output_mode: str = "cli",
) -> dict:
    """
    Replay a transcript at simulated real-time speed and analyze each chunk.
    
    Args:
        transcript_name: Name of the transcript to replay.
        speed_factor: Speed multiplier (1.0 = real-time, 0.5 = half speed).
        output_mode: "cli" for terminal output, "json" for structured output.
    
    Returns:
        Dict with nudges, latency measurements, and summary.
    """
    reset_nudge_state()
    
    transcript = SAMPLE_TRANSCRIPTS.get(transcript_name, SAMPLE_TRANSCRIPTS["cooperative"])
    
    all_nudges = []
    all_suppressed = []
    latency_measurements = []
    
    print(f"\n{'='*70}")
    print(f"  REAL-TIME TRANSCRIPT REPLAY: {transcript_name}")
    print(f"  Speed: {speed_factor}x | Chunks: {len(transcript)} | Mode: {output_mode}")
    print(f"{'='*70}\n")
    
    for i, chunk in enumerate(transcript):
        # Simulate real-time delay
        if i > 0:
            prev_time = _parse_time(transcript[i-1]["time"])
            curr_time = _parse_time(chunk["time"])
            delay = (curr_time - prev_time) / speed_factor
            if delay > 0:
                time.sleep(delay)
        
        print(f"[{chunk['time']}] {chunk['speaker'].upper()}: {chunk['text'][:80]}...")
        
        # === Stage 1: Signal Detection ===
        t0 = time.time()
        signal_result = detect_signals(
            transcript_chunk=chunk["text"],
            agent_or_customer=chunk["speaker"],
        )
        t1 = time.time()
        detection_ms = (t1 - t0) * 1000
        
        signal_data = json.loads(signal_result)
        
        latency_tracker.record("signal_detection", detection_ms, {
            "chunk_index": i, "timestamp": chunk["time"]
        })
        
        # === Stage 2: Nudge Emission ===
        for signal in signal_data.get("signals", []):
            t2 = time.time()
            nudge_result = emit_nudge(
                signal_type=signal["signal_type"],
                confidence=signal["confidence"],
                evidence="; ".join(signal.get("evidence", [])),
                call_timestamp=chunk["time"],
            )
            t3 = time.time()
            emission_ms = (t3 - t2) * 1000
            
            nudge_data = json.loads(nudge_result)
            
            total_ms = (t3 - t0) * 1000
            
            latency_tracker.record("nudge_emission", emission_ms, {
                "signal_type": signal["signal_type"]
            })
            latency_tracker.record("end_to_end", total_ms, {
                "chunk_index": i, "signal_type": signal["signal_type"]
            })
            
            latency_measurements.append({
                "chunk_index": i,
                "timestamp": chunk["time"],
                "signal_type": signal["signal_type"],
                "detection_ms": round(detection_ms, 2),
                "emission_ms": round(emission_ms, 2),
                "total_ms": round(total_ms, 2),
            })
            
            if nudge_data.get("emitted"):
                all_nudges.append(nudge_data)
                priority_icon = {"high": "[HIGH]", "medium": "[MEDIUM]", "low": "[LOW]"}.get(nudge_data.get("priority", ""), "[INFO]")
                print(f"  {priority_icon} NUDGE [{nudge_data['signal']}] (conf={nudge_data['confidence']}): {nudge_data['nudge'][:80]}")
            else:
                all_suppressed.append(nudge_data)
                print(f"   SUPPRESSED: {nudge_data.get('reason', 'unknown')}")
    
    # === Summary ===
    print(f"\n{'='*70}")
    print(f"  REPLAY COMPLETE")
    print(f"{'='*70}")
    print(f"  Chunks processed: {len(transcript)}")
    print(f"  Nudges emitted:   {len(all_nudges)}")
    print(f"  Nudges suppressed: {len(all_suppressed)}")
    
    if latency_measurements:
        totals = [m["total_ms"] for m in latency_measurements]
        totals.sort()
        n = len(totals)
        p50 = totals[n // 2]
        p95 = totals[int(n * 0.95)]
        print(f"  P50 latency: {p50:.2f} ms")
        print(f"  P95 latency: {p95:.2f} ms")
    
    print(f"{'='*70}\n")
    
    return {
        "transcript_name": transcript_name,
        "chunks_processed": len(transcript),
        "nudges_emitted": all_nudges,
        "nudges_suppressed": all_suppressed,
        "latency_measurements": latency_measurements,
    }


def _parse_time(time_str: str) -> float:
    """Parse HH:MM:SS to seconds."""
    parts = time_str.split(":")
    h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
    return h * 3600 + m * 60 + s


def save_results(results: dict, output_dir: str = "evidence"):
    """Save replay results to evidence directory."""
    out_path = Path(output_dir) / "logs"
    out_path.mkdir(parents=True, exist_ok=True)
    
    # Save full results
    filepath = out_path / f"replay_{results['transcript_name']}_{int(time.time())}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to {filepath}")
    
    # Save latency data
    latency_tracker.save(output_dir)


if __name__ == "__main__":
    # Allow selecting transcript from command line
    name = sys.argv[1] if len(sys.argv) > 1 else "cooperative"
    speed = float(sys.argv[2]) if len(sys.argv) > 2 else 0.3  # Fast for demo
    
    available = list(SAMPLE_TRANSCRIPTS.keys())
    
    if name == "all":
        for transcript_name in available:
            results = replay_transcript(transcript_name, speed_factor=speed)
            save_results(results)
    elif name in available:
        results = replay_transcript(name, speed_factor=speed)
        save_results(results)
    else:
        print(f"Available transcripts: {', '.join(available)}")
        print(f"Usage: python -m realtime_nudges.stream_replay [name|all] [speed]")


