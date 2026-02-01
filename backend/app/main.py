"""FastAPI application entry point."""

import logging
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
from fastapi import File, FastAPI, HTTPException, UploadFile

# Load .env from backend/ directory (works regardless of CWD)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
from fastapi.middleware.cors import CORSMiddleware

from app.models.message import ChatRequest, IngestRequest, IngestResponse
from app.services.samples import get_sample_names, load_sample
from app.services.chat import chat as chat_service
from app.services.parser import parse_file, parse_paste
from app.services.pipeline import process_session
from app.store import store

app = FastAPI(
    title="Chat Context Distiller",
    description="AI-powered context extraction from group chat conversations",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/ingest", response_model=IngestResponse)
async def ingest_paste(body: IngestRequest) -> IngestResponse:
    """Ingest chat log from pasted text."""
    messages = parse_paste(body.text)
    if not messages:
        raise HTTPException(status_code=400, detail="No messages could be parsed from the text")
    session_id = str(uuid.uuid4())
    store.put(session_id, messages)
    authors = list(dict.fromkeys(m.author for m in messages))
    return IngestResponse(session_id=session_id, message_count=len(messages), authors=authors)


@app.post("/api/ingest/upload", response_model=IngestResponse)
async def ingest_upload(file: UploadFile = File(...)) -> IngestResponse:
    """Ingest chat log from uploaded file (.txt, .json, .csv)."""
    suffix = Path((file.filename or "").lower()).suffix
    if suffix not in [".txt", ".json", ".csv"]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported format. Use .txt, .json, or .csv",
        )
    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    try:
        messages = parse_file(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    if not messages:
        raise HTTPException(status_code=400, detail="No messages could be parsed from the file")
    session_id = str(uuid.uuid4())
    store.put(session_id, messages)
    authors = list(dict.fromkeys(m.author for m in messages))
    return IngestResponse(session_id=session_id, message_count=len(messages), authors=authors)


@app.get("/api/samples")
async def list_samples():
    """List available sample chat datasets for demos."""
    return {"samples": get_sample_names()}


@app.get("/api/samples/{name}")
async def get_sample(name: str):
    """Get sample chat content by name (e.g. hackathon, study_group, startup_channel)."""
    content = load_sample(name)
    if content is None:
        raise HTTPException(status_code=404, detail="Sample not found")
    return {"name": name, "text": content}


@app.get("/api/sessions")
async def list_sessions():
    """List all session IDs."""
    return {"sessions": store.list_sessions()}


@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """Get raw messages for a session."""
    messages = store.get(session_id)
    if messages is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "message_count": len(messages),
        "messages": [m.model_dump(mode="json") for m in messages],
    }


@app.post("/api/process/{session_id}")
async def process_chat(session_id: str):
    """Run embedding, clustering, and noise filtering on a session."""
    messages = store.get(session_id)
    if messages is None:
        raise HTTPException(status_code=404, detail="Session not found")
    result = process_session(session_id, messages)
    store.put_processed(session_id, result)
    return result


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session with raw messages and processed result (if available)."""
    messages = store.get(session_id)
    if messages is None:
        raise HTTPException(status_code=404, detail="Session not found")
    out = {
        "session_id": session_id,
        "message_count": len(messages),
        "messages": [m.model_dump(mode="json") for m in messages],
    }
    processed = store.get_processed(session_id)
    if processed:
        out["processed"] = processed
    return out


@app.get("/api/sessions/{session_id}/decisions")
async def get_decisions(session_id: str):
    """Get all extracted decisions across topics."""
    processed = store.get_processed(session_id)
    if processed is None:
        raise HTTPException(status_code=404, detail="Session not found or not yet processed")
    decisions = []
    for ext in processed.get("extractions", []):
        topic = ext.get("topic_name", "")
        for d in ext.get("extraction", {}).get("decisions", []):
            decisions.append({**d, "topic": topic})
    return {"session_id": session_id, "decisions": decisions}


@app.get("/api/sessions/{session_id}/action-items")
async def get_action_items(session_id: str, assignee: Optional[str] = None):
    """Get all extracted action items. Optional filter by assignee."""
    processed = store.get_processed(session_id)
    if processed is None:
        raise HTTPException(status_code=404, detail="Session not found or not yet processed")
    items = []
    for ext in processed.get("extractions", []):
        topic = ext.get("topic_name", "")
        for a in ext.get("extraction", {}).get("action_items", []):
            if assignee and (a.get("assignee") or "").lower() != assignee.lower():
                continue
            items.append({**a, "topic": topic})
    return {"session_id": session_id, "action_items": items}


@app.post("/api/sessions/{session_id}/chat")
async def chat_endpoint(session_id: str, body: ChatRequest):
    """Ask a question about the session. Uses ChromaDB retrieval + Mistral."""
    if store.get(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    answer = chat_service(session_id, body.question)
    return {"answer": answer}


@app.get("/health")
async def health() -> dict:
    """Health check."""
    return {"status": "ok"}
