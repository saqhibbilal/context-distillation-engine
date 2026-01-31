"""FastAPI application entry point."""

import tempfile
import uuid
from pathlib import Path

from fastapi import File, FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.models.message import IngestRequest, IngestResponse
from app.services.parser import parse_file, parse_paste
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


@app.get("/health")
async def health() -> dict:
    """Health check."""
    return {"status": "ok"}
