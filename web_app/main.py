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

# Agent map for routing
AGENT_MAP = {
    "loan": loan_qualification_agent,
    "philippines": philippines_voice_agent,
    "indonesia": indonesia_voice_agent,
    "nudge": realtime_nudge_agent,
}

# Store conversation transcripts
transcripts = {}  # session_id -> list of messages

# WebSocket connections for nudge dashboard
nudge_clients: list[WebSocket] = []


async def run_agent_turn(agent_name: str, session_id: str, user_message: str) -> str:
    """Run a single turn with the specified ADK agent."""
    agent = AGENT_MAP.get(agent_name, loan_qualification_agent)
    
    runner = Runner(
        agent=agent,
        app_name="quickfund_assessment",
        session_service=session_service,
    )
    
    user_content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=user_message)],
    )
    
    start_time = time.time()
    response_text = ""
    tool_calls_log = []
    
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
        if hasattr(event, 'function_calls') and event.function_calls:
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
    
    end_time = time.time()
    latency_ms = (end_time - start_time) * 1000
    latency_tracker.record("agent_turn", latency_ms, {"agent": agent_name})
    
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
    })
    
    return response_text


# === Page Routes ===

@app.get("/")
async def index(request: Request):
    """Main voice agent page (Q1)."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/philippines")
async def philippines_page(request: Request):
    """Philippines bot page (Q3)."""
    return templates.TemplateResponse("philippines.html", {"request": request})


@app.get("/indonesia")
async def indonesia_page(request: Request):
    """Indonesia bot page (Q3)."""
    return templates.TemplateResponse("indonesia.html", {"request": request})


@app.get("/dashboard")
async def dashboard_page(request: Request):
    """Real-time nudge dashboard (Q4)."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


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
        response = await run_agent_turn(agent_name, session_id, message)
        return JSONResponse({
            "response": response,
            "session_id": session_id,
            "agent": agent_name,
        })
    except Exception as e:
        logger.error(f"Agent error: {e}", exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)


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
        response = await run_agent_turn("nudge", session_id, prompt)
        
        # Broadcast to WebSocket clients
        nudge_data = {
            "timestamp": timestamp,
            "chunk": chunk,
            "speaker": speaker,
            "analysis": response,
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
                    response = await run_agent_turn("nudge", f"ws_{int(time.time())}", prompt)
                    
                    await websocket.send_json({
                        "timestamp": timestamp,
                        "chunk": chunk,
                        "analysis": response,
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
