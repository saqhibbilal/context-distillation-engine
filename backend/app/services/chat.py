"""Chat/query over session context using ChromaDB retrieval + Mistral."""

import logging
import os

from app.services.embeddings import embed_text
from app.services.vector_store import query_similar_safe

logger = logging.getLogger(__name__)


def _format_context(chunks: list[dict]) -> str:
    out = []
    for c in chunks:
        meta = c.get("metadata", {})
        author = meta.get("author", "Unknown")
        content = meta.get("content", "")
        ts = meta.get("timestamp", "")
        out.append(f"[{ts}] {author}: {content}")
    return "\n".join(out)


def answer_question(session_id: str, question: str, chunks: list[dict]) -> str:
    """Use Mistral to answer a question given retrieved chunks."""
    api_key = os.environ.get("MISTRAL_API_KEY", "").strip()
    if not api_key:
        logger.warning("MISTRAL_API_KEY not set")
        return "API key not configured. Set MISTRAL_API_KEY in backend/.env"

    try:
        from mistralai import Mistral
        client = Mistral(api_key=api_key)
    except Exception as e:
        logger.exception("Mistral client init failed: %s", e)
        return "Failed to connect to AI service."

    context = _format_context(chunks)
    if not context:
        return "No relevant context found. Try a different question."

    prompt = f"""You are answering questions about a team chat. Use only the context below. Be concise.

Context:
{context}

Question: {question}

Answer (brief, based only on the context):"""

    try:
        response = client.chat.complete(
            model="mistral-small-2409",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=400,
        )
        answer = response.choices[0].message.content or "No answer generated."
        logger.info("Chat answer generated for session %s", session_id[:8])
        return answer.strip()
    except Exception as e:
        logger.exception("Chat answer failed: %s", e)
        return f"Error: {str(e)}"


def chat(session_id: str, question: str) -> str:
    """Embed question, retrieve similar chunks, answer with Mistral."""
    if not question or not question.strip():
        return "Please ask a question."
    q = question.strip()
    try:
        emb = embed_text(q)
        chunks = query_similar_safe(session_id, emb, n_results=8)
        return answer_question(session_id, q, chunks)
    except Exception as e:
        logger.exception("Chat failed: %s", e)
        return f"Error: {str(e)}"
