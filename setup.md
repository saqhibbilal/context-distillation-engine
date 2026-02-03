# Setup Guide

## Prerequisites

- Python 3.11
- Node.js 18+
- Mistral API key ([console.mistral.ai](https://console.mistral.ai))

---

## 1. Backend

```bash
cd backend
pip install -r requirements.txt
```

Create `backend/.env`:

```
MISTRAL_API_KEY=your_key_here
```

Run:

```bash
py -3.11 -m uvicorn app.main:app --reload --port 8000
```

Or: `python -m uvicorn app.main:app --reload --port 8000` (use the same Python as pip).

---

## 2. Frontend

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

---

## 3. Discord Bot (optional)

Create a bot at [Discord Developer Portal](https://discord.com/developers/applications). Create `discord-bot/.env`:

```
DISCORD_BOT_TOKEN=your_bot_token
BACKEND_URL=http://localhost:8000
```

Run (with backend already running):

```bash
cd discord-bot
pip install -r requirements.txt
python bot.py
```

Use `/distill` in a channel.

---

## Quick Start

1. Clone the repo
2. `cd backend` → pip install → add .env with MISTRAL_API_KEY → run uvicorn
3. `cd frontend` → npm install → npm run dev
4. Open http://localhost:5173 → Ingest → paste or upload chat → Analyze & Extract Context
