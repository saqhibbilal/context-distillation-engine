"""Message and ingestion models."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ChatSource(str, Enum):
    """Source of chat data."""

    PASTE = "paste"
    UPLOAD = "upload"
    DISCORD = "discord"


class Message(BaseModel):
    """A single chat message with metadata."""

    author: str = Field(..., description="Message author/username")
    content: str = Field(..., description="Raw message content")
    timestamp: Optional[datetime] = Field(None, description="Message timestamp")
    source: ChatSource = Field(default=ChatSource.PASTE)

    def to_display(self) -> str:
        """Format for display in clustered view."""
        ts = self.timestamp.strftime("%Y-%m-%d %H:%M") if self.timestamp else ""
        return f"[{ts}] {self.author}: {self.content}"


class IngestRequest(BaseModel):
    """Request body for paste ingestion."""

    text: str = Field(..., min_length=1, description="Raw chat log text to parse")


class IngestResponse(BaseModel):
    """Response after successful ingestion."""

    session_id: str
    message_count: int
    authors: list[str]
