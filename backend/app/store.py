"""In-memory session store for ingested chats."""

from typing import Any, Optional

from app.models.message import Message


class SessionStore:
    """Simple in-memory store for chat sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, list[Message]] = {}
        self._processed: dict[str, dict[str, Any]] = {}

    def put(self, session_id: str, messages: list[Message]) -> None:
        """Store messages for a session."""
        self._sessions[session_id] = messages

    def get(self, session_id: str) -> Optional[list[Message]]:
        """Retrieve messages for a session."""
        return self._sessions.get(session_id)

    def put_processed(self, session_id: str, result: dict[str, Any]) -> None:
        """Store processed pipeline result."""
        self._processed[session_id] = result

    def get_processed(self, session_id: str) -> Optional[dict[str, Any]]:
        """Retrieve processed result for a session."""
        return self._processed.get(session_id)

    def delete(self, session_id: str) -> bool:
        """Remove a session. Returns True if it existed."""
        existed = False
        if session_id in self._sessions:
            del self._sessions[session_id]
            existed = True
        if session_id in self._processed:
            del self._processed[session_id]
            existed = True
        return existed

    def list_sessions(self) -> list[str]:
        """List all session IDs."""
        return list(self._sessions.keys())


# Global instance
store = SessionStore()
