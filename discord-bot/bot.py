"""
Context Distiller Discord Bot.
Invite to a server to distill channel context on demand.
Requires: backend running, DISCORD_BOT_TOKEN, BACKEND_URL in .env
"""

import os
from datetime import datetime

import discord
from discord import app_commands
from dotenv import load_dotenv
import httpx

load_dotenv()

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


def _format_message(msg: discord.Message) -> str:
    """Format a Discord message for our parser."""
    ts = msg.created_at.strftime("%Y-%m-%d %H:%M")
    author = msg.author.display_name or str(msg.author)
    content = (msg.content or "").strip()
    if not content:
        return None
    return f"[{ts}] {author}: {content}"


async def _fetch_channel_messages(channel: discord.TextChannel, limit: int = 100) -> list[str]:
    """Fetch recent messages and format for ingestion."""
    lines = []
    async for msg in channel.history(limit=limit, oldest_first=True):
        if msg.author.bot:
            continue
        line = _format_message(msg)
        if line:
            lines.append(line)
    return lines


def _call_backend(text: str) -> dict | None:
    """Ingest and process via backend API."""
    with httpx.Client(timeout=60.0) as http:
        r = http.post(f"{BACKEND_URL}/api/ingest", json={"text": text})
        if r.status_code != 200:
            return None
        data = r.json()
        session_id = data.get("session_id")
        if not session_id:
            return None
        r2 = http.post(f"{BACKEND_URL}/api/process/{session_id}")
        if r2.status_code != 200:
            return None
        return r2.json()


def _build_summary(result: dict) -> str:
    """Build a concise Discord summary from processed result."""
    parts = []
    extractions = result.get("extractions", [])
    all_decisions = []
    all_actions = []
    for e in extractions:
        ext = e.get("extraction", {})
        for d in ext.get("decisions", []):
            all_decisions.append(d.get("description", ""))
        for a in ext.get("action_items", []):
            task = a.get("task", "")
            assignee = a.get("assignee", "")
            if assignee:
                all_actions.append(f"- {task} (→ {assignee})")
            else:
                all_actions.append(f"- {task}")
    if all_decisions:
        parts.append("**Decisions**\n" + "\n".join(f"• {d}" for d in all_decisions[:5]))
    if all_actions:
        parts.append("**Action Items**\n" + "\n".join(all_actions[:5]))
    if not parts:
        return "No decisions or action items extracted from this conversation."
    return "\n\n".join(parts)


@tree.command(name="distill", description="Distill recent channel messages into decisions and action items")
@app_commands.describe(limit="Number of messages to fetch (default 50)")
async def distill(interaction: discord.Interaction, limit: int = 50):
    await interaction.response.defer(ephemeral=False)
    channel = interaction.channel
    if not isinstance(channel, discord.TextChannel):
        await interaction.followup.send("This command works only in text channels.", ephemeral=True)
        return
    lines = await _fetch_channel_messages(channel, limit=min(limit, 100))
    if not lines:
        await interaction.followup.send("No messages to distill in this channel.")
        return
    text = "\n".join(lines)
    result = _call_backend(text)
    if result is None:
        await interaction.followup.send(
            "Failed to process. Ensure the backend is running at " + BACKEND_URL,
            ephemeral=True,
        )
        return
    summary = _build_summary(result)
    msg_count = result.get("message_count", 0)
    embed = discord.Embed(
        title="Context Distilled",
        description=summary,
        color=0x5865F2,
        timestamp=datetime.utcnow(),
    )
    embed.set_footer(text=f"{msg_count} messages processed")
    await interaction.followup.send(embed=embed)


@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user} (Context Distiller Bot)")


def main():
    if not DISCORD_BOT_TOKEN:
        print("Set DISCORD_BOT_TOKEN in .env")
        return
    client.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
