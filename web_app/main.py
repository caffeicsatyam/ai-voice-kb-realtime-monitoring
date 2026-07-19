"""
FastAPI Web Application
Serves the voice agent UI and provides API endpoints for all assessment questions.
"""
import json
import os
import sys
import time
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from adk_app.agents.loan_qualification_agent import loan_qualification_agent
from adk_app.agents.philippines_voice_agent import philippines_voice_agent
from adk_app.agents.indonesia_voice_agent import indonesia_voice_agent
from adk_app.agents.realtime_nudge_agent import realtime_nudge_agent
from adk_app.callbacks.citation_guard import log_citation_usage
from adk_app.callbacks.latency_logger import latency_tracker
from web_app.langchain_middleware import (
    GroqFallbackUnavailable,
    LangChainGroqFallbackMiddleware,
)
from web_app.guardrail_middleware import (
    InputGuard,
    OutputGuard,
    GuardrailLogger,
    LLMGuard,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === FastAPI App ===
app = FastAPI(
    title="QuickFund AI Voice Agent Assessment",
    description="Google ADK-powered voice agent for small business loan qualification",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
web_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(web_dir / "static")), name="static")
templates = Jinja2Templates(directory=str(web_dir / "templates"))

# === ADK Session Management ===
session_service = InMemorySessionService()
groq_fallback = LangChainGroqFallbackMiddleware()
input_guard = InputGuard()
output_guard = OutputGuard()
guardrail_logger = GuardrailLogger()
llm_guard = LLMGuard()

# Agent map for routing
AGENT_MAP = {
    "loan": loan_qualification_agent,
    "philippines": philippines_voice_agent,
    "indonesia": indonesia_voice_agent,
    "nudge": realtime_nudge_agent,
}

# Store conversation transcripts
transcripts = {}  # session_id -> list of messages
last_turn_fallback = {}  # session_id -> bool

# WebSocket connections for nudge dashboard
nudge_clients: list[WebSocket] = []


async def run_agent_turn(agent_name: str, session_id: str, user_message: str) -> dict:
    """Run a single turn with ADK, falling back to LangChain/Groq on failure.

    Returns a dict with keys:
        response  – the final text to send to the user
        fallback  – whether the Groq fallback was used
        guardrail – dict with input/output guard metadata (may be empty)
    """
    guard_meta: dict = {}

    # --- Layer 1: Regex InputGuard ---
    input_result = input_guard.check(user_message)
    if input_result.blocked:
        guardrail_logger.log(
            stage="input_regex",
            guard_result=input_result,
            agent_name=agent_name,
            session_id=session_id,
            snippet=user_message,
        )
        guard_meta = {
            "input_blocked": True,
            "category": input_result.category,
            "reason": input_result.reason,
            "layer": "regex",
        }
        return {
            "response": input_result.reason,
            "fallback": False,
            "guardrail": guard_meta,
        }

    # --- Layer 2: LLM InputGuard (only if regex passed) ---
    llm_input_result = await llm_guard.check_input(user_message)
    if llm_input_result.blocked:
        guardrail_logger.log(
            stage="input_llm",
            guard_result=llm_input_result,
            agent_name=agent_name,
            session_id=session_id,
            snippet=user_message,
        )
        guard_meta = {
            "input_blocked": True,
            "category": llm_input_result.category,
            "reason": llm_input_result.reason,
            "layer": "llm",
        }
        return {
            "response": llm_input_result.reason,
            "fallback": False,
            "guardrail": guard_meta,
        }

    agent = AGENT_MAP.get(agent_name, loan_qualification_agent)
    original_model = agent.model

    user_content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=user_message)],
    )

    start_time = time.time()
    response_text = ""
    tool_calls_log = []
    used_fallback = False
    
    models_to_try = [original_model, "gemini-3.1-flash-lite", "gemini-3.0-flash", "gemini-2.5-flash", "gemini-2.0-flash-lite"]
    success = False
    last_exc = None

    for current_model in models_to_try:
        agent.model = current_model
        runner = Runner(
            agent=agent,
            app_name="quickfund_assessment",
            session_service=session_service,
            auto_create_session=True,
        )
        
        try:
            async for event in runner.run_async(
                user_id="demo_user",
                session_id=session_id,
                new_message=user_content,
            ):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        response_text = "\n".join(
                            part.text for part in event.content.parts if part.text
                        )

                # Log tool calls for evidence
                if hasattr(event, "function_calls") and event.function_calls:
                    for fc in event.function_calls:
                        tool_call = {
                            "tool": fc.name,
                            "args": dict(fc.args) if fc.args else {},
                            "timestamp": datetime.now().isoformat(),
                        }
                        tool_calls_log.append(tool_call)

                        # Log KB retrievals specifically
                        if fc.name == "retrieve_kb":
                            log_citation_usage(fc.name, dict(fc.args) if fc.args else {}, "")
            
            success = True
            break
        except Exception as exc:
            logger.warning(f"ADK agent failed with model {current_model}: {exc}")
            last_exc = exc
            continue

    agent.model = original_model

    if not success:
        logger.warning(
            "All ADK models failed; attempting LangChain Groq fallback: %s",
            last_exc,
            exc_info=True,
        )
        try:
            response_text = await groq_fallback.generate(
                agent_name=agent_name,
                session_id=session_id,
                user_message=user_message,
                failure_reason=f"{type(exc).__name__}: {exc}",
            )
            used_fallback = True
            tool_calls_log.append({
                "tool": "langchain_groq_fallback",
                "args": {
                    "agent": agent_name,
                    "model": groq_fallback.model,
                },
                "timestamp": datetime.now().isoformat(),
            })
        except GroqFallbackUnavailable as fallback_exc:
            logger.error("LangChain Groq fallback unavailable: %s", fallback_exc)
            raise exc from fallback_exc

    end_time = time.time()
    latency_ms = (end_time - start_time) * 1000
    latency_tracker.record("agent_turn", latency_ms, {
        "agent": agent_name,
        "fallback": used_fallback,
    })
    last_turn_fallback[session_id] = used_fallback

    # --- Layer 1: Regex OutputGuard ---
    response_text, output_result = output_guard.apply(response_text)
    if output_result.blocked or output_result.warnings:
        guardrail_logger.log(
            stage="output_regex",
            guard_result=output_result,
            agent_name=agent_name,
            session_id=session_id,
            snippet=response_text,
        )
        guard_meta = {
            "output_blocked": output_result.blocked,
            "output_flagged": bool(output_result.warnings),
            "category": output_result.category,
            "reason": output_result.reason,
            "layer": "regex",
        }

    # --- Layer 2: LLM OutputGuard (only if regex didn't hard-block) ---
    if not output_result.blocked:
        llm_output_result = await llm_guard.check_output(response_text)
        if llm_output_result.blocked:
            guardrail_logger.log(
                stage="output_llm",
                guard_result=llm_output_result,
                agent_name=agent_name,
                session_id=session_id,
                snippet=response_text,
            )
            response_text = output_guard.SAFE_FALLBACK
            guard_meta = {
                "output_blocked": True,
                "output_flagged": False,
                "category": llm_output_result.category,
                "reason": llm_output_result.reason,
                "layer": "llm",
            }
        elif llm_output_result.warnings:
            guardrail_logger.log(
                stage="output_llm",
                guard_result=llm_output_result,
                agent_name=agent_name,
                session_id=session_id,
                snippet=response_text,
            )
            for warning in llm_output_result.warnings:
                if warning not in response_text:
                    response_text += f"\n\n*{warning}*"
            guard_meta = {
                "output_blocked": False,
                "output_flagged": True,
                "category": llm_output_result.category,
                "reason": llm_output_result.reason,
                "layer": "llm",
            }

    # Store transcript
    if session_id not in transcripts:
        transcripts[session_id] = []
    transcripts[session_id].append({
        "role": "user",
        "content": user_message,
        "timestamp": datetime.now().isoformat(),
    })
    transcripts[session_id].append({
        "role": "agent",
        "content": response_text,
        "timestamp": datetime.now().isoformat(),
        "tool_calls": tool_calls_log,
        "latency_ms": round(latency_ms, 2),
        "fallback": used_fallback,
        "guardrail": guard_meta,
    })

    return {
        "response": response_text,
        "fallback": used_fallback,
        "guardrail": guard_meta,
    }

# === Page Routes ===

@app.get("/")
async def index(request: Request):
    """Main voice agent page (Q1)."""
    return templates.TemplateResponse(request, "index.html")


@app.get("/philippines")
async def philippines_page(request: Request):
    """Philippines bot page (Q3)."""
    return templates.TemplateResponse(request, "philippines.html")


@app.get("/indonesia")
async def indonesia_page(request: Request):
    """Indonesia bot page (Q3)."""
    return templates.TemplateResponse(request, "indonesia.html")


@app.get("/dashboard")
async def dashboard_page(request: Request):
    """Real-time nudge dashboard (Q4)."""
    return templates.TemplateResponse(request, "dashboard.html")


# === API Routes ===

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    """
    Text chat with an ADK agent.
    Body: { "message": "...", "agent": "loan|philippines|indonesia", "session_id": "..." }
    """
    body = await request.json()
    message = body.get("message", "")
    agent_name = body.get("agent", "loan")
    session_id = body.get("session_id", f"session_{int(time.time())}")
    
    if not message:
        return JSONResponse({"error": "Message is required"}, status_code=400)
    
    try:
        result = await run_agent_turn(agent_name, session_id, message)
        return JSONResponse({
            "response": result["response"],
            "session_id": session_id,
            "agent": agent_name,
            "fallback": result["fallback"],
            "guardrail": result.get("guardrail", {}),
        })
    except Exception as e:
        logger.error(f"Agent error: {e}", exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/nudge-event")
async def nudge_event_endpoint(request: Request):
    """
    Broadcast a deterministic replay event to connected nudge dashboards.
    Body may contain a transcript chunk, emitted nudge, or suppression event.
    """
    body = await request.json()
    body.setdefault("received_at", datetime.now().isoformat())

    disconnected = []
    for client in list(nudge_clients):
        try:
            await client.send_json(body)
        except Exception:
            disconnected.append(client)

    for client in disconnected:
        if client in nudge_clients:
            nudge_clients.remove(client)

    return JSONResponse({
        "broadcast": True,
        "clients": len(nudge_clients),
        "event_type": body.get("event_type", "nudge"),
    })

@app.post("/api/nudge-analyze")
async def nudge_analyze_endpoint(request: Request):
    """
    Analyze a transcript chunk for nudges (Q4).
    Body: { "chunk": "...", "timestamp": "00:01:30", "speaker": "customer" }
    """
    body = await request.json()
    chunk = body.get("chunk", "")
    timestamp = body.get("timestamp", "")
    speaker = body.get("speaker", "unknown")
    session_id = body.get("session_id", f"nudge_{int(time.time())}")
    
    if not chunk:
        return JSONResponse({"error": "Chunk is required"}, status_code=400)
    
    # Use the nudge agent
    prompt = f"Analyze this transcript chunk for signals. Speaker: {speaker}. Timestamp: {timestamp}. Chunk: \"{chunk}\""
    
    try:
        result = await run_agent_turn("nudge", session_id, prompt)
        
        analysis_text = result["response"]
        is_clean = "no actionable signals" in analysis_text.lower()
        
        # Broadcast to WebSocket clients
        nudge_data = {
            "timestamp": timestamp,
            "chunk": chunk,
            "speaker": speaker,
            "analysis": analysis_text,
            "emitted": not is_clean,
            "event_type": "nudge" if not is_clean else "suppressed",
            "reason": analysis_text if is_clean else None,
            "received_at": datetime.now().isoformat(),
        }
        for client in nudge_clients:
            try:
                await client.send_json(nudge_data)
            except Exception:
                pass
        
        return JSONResponse(nudge_data)
    except Exception as e:
        logger.error(f"Nudge analysis error: {e}", exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/transcript/{session_id}")
async def get_transcript(session_id: str):
    """Get conversation transcript for a session."""
    if session_id not in transcripts:
        return JSONResponse({"error": "Session not found"}, status_code=404)
    return JSONResponse({
        "session_id": session_id,
        "messages": transcripts[session_id],
    })


@app.get("/api/transcripts")
async def list_transcripts():
    """List all session IDs with message counts."""
    return JSONResponse({
        "sessions": [
            {"session_id": sid, "message_count": len(msgs)}
            for sid, msgs in transcripts.items()
        ]
    })


@app.get("/api/latency")
async def get_latency():
    """Get latency statistics."""
    stages = set(e["stage"] for e in latency_tracker.measurements)
    stats = {stage: latency_tracker.get_stats(stage) for stage in stages}
    stats["overall"] = latency_tracker.get_stats()
    return JSONResponse(stats)


@app.get("/api/guardrail-stats")
async def get_guardrail_stats():
    """Get guardrail event counts by category."""
    return JSONResponse({
        "guardrail_events": guardrail_logger.stats,
    })


@app.get("/api/evidence-logs")
async def get_evidence_logs():
    """List evidence log files."""
    log_dir = Path("evidence/logs")
    if not log_dir.exists():
        return JSONResponse({"logs": []})
    
    logs = []
    for f in log_dir.glob("*.jsonl"):
        lines = f.read_text(encoding="utf-8").strip().split("\n")
        logs.append({
            "filename": f.name,
            "entries": len(lines),
            "size_bytes": f.stat().st_size,
        })
    return JSONResponse({"logs": logs})


# === WebSocket for Nudge Dashboard ===

@app.websocket("/ws/nudges")
async def nudge_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time nudge streaming."""
    await websocket.accept()
    nudge_clients.append(websocket)
    logger.info(f"Nudge dashboard connected. Total clients: {len(nudge_clients)}")
    
    try:
        while True:
            data = await websocket.receive_text()
            # Client can send transcript chunks via WebSocket too
            try:
                msg = json.loads(data)
                chunk = msg.get("chunk", "")
                timestamp = msg.get("timestamp", "")
                speaker = msg.get("speaker", "unknown")
                
                if chunk:
                    prompt = f"Analyze this transcript chunk for signals. Speaker: {speaker}. Timestamp: {timestamp}. Chunk: \"{chunk}\""
                    result = await run_agent_turn("nudge", f"ws_{int(time.time())}", prompt)
                    
                    await websocket.send_json({
                        "timestamp": timestamp,
                        "chunk": chunk,
                        "analysis": result["response"],
                    })
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        nudge_clients.remove(websocket)
        logger.info(f"Nudge dashboard disconnected. Total clients: {len(nudge_clients)}")


# === Save transcripts on shutdown ===

@app.on_event("shutdown")
async def save_transcripts():
    """Save all transcripts to evidence directory on shutdown."""
    transcript_dir = Path("evidence/transcripts")
    transcript_dir.mkdir(parents=True, exist_ok=True)
    
    for session_id, messages in transcripts.items():
        filepath = transcript_dir / f"{session_id}.jsonl"
        with open(filepath, "w", encoding="utf-8") as f:
            for msg in messages:
                f.write(json.dumps(msg, ensure_ascii=False) + "\n")
    
    # Save latency data
    latency_tracker.save()
    logger.info(f"Saved {len(transcripts)} transcripts to evidence/transcripts/")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
