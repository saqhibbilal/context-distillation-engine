"""Sentence-level embeddings for chat messages."""

from typing import Optional

from app.models.message import Message


# Lazy-loaded model
_model: Optional["SentenceTransformer"] = None


def _get_model() -> "SentenceTransformer":
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed_text(text: str) -> list[float]:
    """Embed a single text string. Returns 384-dim vector."""
    if not text:
        return []
    model = _get_model()
    emb = model.encode([text], convert_to_numpy=True)
    return emb[0].tolist()


def embed_messages(messages: list[Message]) -> list[list[float]]:
    """
    Embed a list of messages. Each message is encoded as a single vector.
    Returns list of 384-dim vectors.
    """
    if not messages:
        return []
    texts = [m.content for m in messages]
    model = _get_model()
    embeddings = model.encode(texts, convert_to_numpy=True)
    return [e.tolist() for e in embeddings]
