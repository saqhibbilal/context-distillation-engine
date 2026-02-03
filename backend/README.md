# Chat Context Distiller - Backend

## Phase 1 Part 1: Project Setup + Chat Parsing & Ingestion

### Setup

```bash
cd backend
pip install -r requirements.txt
```

### Run

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

If `python` points to a different Python than `pip` (e.g. pip uses 3.11 but `python` is 3.9), use the same interpreter:
```bash
py -3.11 -m uvicorn app.main:app --reload --port 8000
```
Or: `python3.11 -m uvicorn app.main:app --reload --port 8000` if available.

API docs: http://localhost:8000/docs

### Endpoints

- `POST /api/ingest` — Paste chat text (JSON body: `{"text": "..."}`)
- `POST /api/ingest/upload` — Upload .txt, .json, or .csv file
- `POST /api/process/{session_id}` — Run full pipeline (embed, cluster, filter, Mistral extraction)
- `GET /api/sessions/{session_id}` — Full session (messages + processed if available)
- `GET /api/sessions/{session_id}/messages` — Raw messages only
- `GET /api/sessions/{session_id}/decisions` — All extracted decisions
- `GET /api/sessions/{session_id}/action-items?assignee=X` — Action items, optional assignee filter
- `GET /health` — Health check

### Environment

Create `.env` with `MISTRAL_API_KEY=` (from https://console.mistral.ai/). Without it, clustering runs but extraction is skipped.

### Supported Chat Formats

**Paste (plain text):**
- `[2024-01-15 14:30] Alice: Hello everyone`
- `[14:30] Bob: Sounds good`
- `Alice: Simple author: message format`

**Files:** `.txt` (same as paste), `.json` (Discord-style or `{author, content, timestamp}`), `.csv` (author, content, timestamp columns)

### Full stack (with frontend)

1. Start backend: `cd backend && py -3.11 -m uvicorn app.main:app --reload --port 8000`
2. Start frontend: `cd frontend && npm install && npm run dev`
3. Open http://localhost:5173

### Discord bot (optional)

1. Create bot at https://discord.com/developers/applications
2. Add `discord-bot/.env` with `DISCORD_BOT_TOKEN` and `BACKEND_URL`
3. Run: `cd discord-bot && pip install -r requirements.txt && python bot.py`
4. Use `/distill` in a channel
