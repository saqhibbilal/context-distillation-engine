"""Chat log parsing for multiple formats."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.models.message import ChatSource, Message


# Regex patterns for common chat formats
# Discord-style: [YYYY-MM-DD HH:MM] Author: content
DISCORD_LIKE = re.compile(
    r"\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?)\]\s+([^:]+?):\s*(.*)",
    re.DOTALL,
)

# Simple time + author: [HH:MM] Author: content
SIMPLE_TIME = re.compile(
    r"\[(\d{1,2}:\d{2}(?::\d{2})?)\]\s+([^:]+?):\s*(.*)",
    re.DOTALL,
)

# Author: content (single line, no timestamp)
AUTHOR_COLON = re.compile(r"^([^:]+?):\s*(.+)$", re.MULTILINE)


def _parse_discord_datetime(s: str) -> Optional[datetime]:
    """Parse datetime from Discord-style or simple time string."""
    s = s.strip()
    # Full datetime: 2024-01-15 14:30 or 2024-01-15 14:30:00
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    # Time only: 14:30 or 14:30:00 (use today as date)
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            t = datetime.strptime(s, fmt)
            return t.replace(year=datetime.now().year, month=datetime.now().month, day=datetime.now().day)
        except ValueError:
            continue
    return None


def parse_paste(text: str, source: ChatSource = ChatSource.PASTE) -> list[Message]:
    """
    Parse raw pasted chat text into Message objects.
    Tries multiple formats in order of specificity.
    """
    text = text.strip()
    if not text:
        return []

    messages: list[Message] = []
    seen = set()

    # Try Discord-style first (most specific)
    for m in DISCORD_LIKE.finditer(text):
        ts_str, author, content = m.groups()
        author = author.strip()
        content = content.strip()
        if not author or not content:
            continue
        key = (author, content)
        if key in seen:
            continue
        seen.add(key)
        ts = _parse_discord_datetime(ts_str)
        messages.append(
            Message(
                author=author,
                content=content,
                timestamp=ts,
                source=source,
            )
        )

    if messages:
        return messages

    # Try simple time format
    for m in SIMPLE_TIME.finditer(text):
        ts_str, author, content = m.groups()
        author = author.strip()
        content = content.strip()
        if not author or not content:
            continue
        key = (author, content)
        if key in seen:
            continue
        seen.add(key)
        ts = _parse_discord_datetime(ts_str)
        messages.append(
            Message(
                author=author,
                content=content,
                timestamp=ts,
                source=source,
            )
        )

    if messages:
        return messages

    # Fallback: Author: content (line by line)
    for m in AUTHOR_COLON.finditer(text):
        author, content = m.groups()
        author = author.strip()
        content = content.strip()
        if not author or not content:
            continue
        key = (author, content)
        if key in seen:
            continue
        seen.add(key)
        messages.append(
            Message(
                author=author,
                content=content,
                timestamp=None,
                source=source,
            )
        )

    return messages


def parse_file(file_path: Path, source: ChatSource = ChatSource.UPLOAD) -> list[Message]:
    """
    Parse a chat file (.txt, .json, .csv) into Message objects.
    """
    suffix = file_path.suffix.lower()

    if suffix == ".txt":
        text = file_path.read_text(encoding="utf-8", errors="replace")
        return parse_paste(text, source)

    if suffix == ".json":
        data = json.loads(file_path.read_text(encoding="utf-8", errors="replace"))
        return _parse_json_chat(data, source)

    if suffix == ".csv":
        return _parse_csv_chat(file_path, source)

    raise ValueError(f"Unsupported file format: {suffix}")


def _parse_json_chat(data: dict | list, source: ChatSource) -> list[Message]:
    """
    Parse JSON chat export.
    Supports Discord export format and generic list of {author, content, timestamp}.
    """
    messages: list[Message] = []

    # Discord export: { "messages": [ {...} ] } or flat list
    if isinstance(data, dict):
        items = data.get("messages", [])
    else:
        items = data if isinstance(data, list) else []

    for item in items:
        if isinstance(item, dict):
            author = item.get("author", item.get("username", item.get("user", "Unknown")))
            if isinstance(author, dict):
                author = author.get("name", author.get("username", "Unknown"))
            content = item.get("content", item.get("message", item.get("text", "")))
            ts_raw = item.get("timestamp", item.get("date", item.get("created_at")))
            ts = None
            if ts_raw:
                try:
                    if isinstance(ts_raw, str):
                        ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                    elif isinstance(ts_raw, (int, float)):
                        ts = datetime.fromtimestamp(ts_raw)
                except (ValueError, TypeError):
                    pass
            messages.append(
                Message(author=str(author), content=str(content), timestamp=ts, source=source)
            )

    return messages


def _parse_csv_chat(file_path: Path, source: ChatSource) -> list[Message]:
    """Parse CSV with columns: author, content, timestamp (optional)."""
    import csv

    messages: list[Message] = []
    text = file_path.read_text(encoding="utf-8", errors="replace")
    reader = csv.DictReader(text.splitlines())

    for row in reader:
        author = row.get("author", row.get("Author", row.get("user", "Unknown")))
        content = row.get("content", row.get("Content", row.get("message", "")))
        ts_raw = row.get("timestamp", row.get("Timestamp", row.get("date", "")))
        ts = None
        if ts_raw:
            try:
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            except ValueError:
                try:
                    ts = datetime.strptime(ts_raw, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass
        messages.append(
            Message(author=str(author), content=str(content), timestamp=ts, source=source)
        )

    return messages
