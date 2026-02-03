# Context Distiller - Discord Bot

## Setup

1. Create a bot at https://discord.com/developers/applications
2. Copy the bot token
3. Create `discord-bot/.env`:
   ```
   DISCORD_BOT_TOKEN=your_token
   BACKEND_URL=http://localhost:8000
   ```
4. Invite the bot to your server with scopes: `bot`, `applications.commands`
   Permissions: Read Message History, Send Messages

## Run

1. Start the backend: `cd backend && py -3.11 -m uvicorn app.main:app --reload --port 8000`
2. Run the bot: `cd discord-bot && pip install -r requirements.txt && python bot.py`

## Commands

- `/distill [limit]` - Fetches recent channel messages, sends to backend, replies with decisions and action items
