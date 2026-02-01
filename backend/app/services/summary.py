"""Generate concise prose summary of distilled context."""

import logging
import os

logger = logging.getLogger(__name__)


def generate_summary(extractions: list[dict], full_text: str, max_words: int = 250) -> str:
    """Generate a ~250 word prose summary from extractions + full chat."""
    api_key = os.environ.get("MISTRAL_API_KEY", "").strip()
    if not api_key:
        logger.warning("MISTRAL_API_KEY not set - skipping summary")
        return ""

    try:
        from mistralai import Mistral
        client = Mistral(api_key=api_key)
    except Exception as e:
        logger.exception("Failed to init Mistral client: %s", e)
        return ""

    # Build context from extractions
    parts = []
    for e in extractions:
        ext = e.get("extraction", {})
        topic = e.get("topic_name", "")
        if ext.get("decisions"):
            parts.append(f"[{topic}] Decisions: " + "; ".join(d.get("description", "") for d in ext["decisions"]))
        if ext.get("action_items"):
            parts.append(f"[{topic}] Action items: " + "; ".join(
                f"{a.get('task', '')} (→{a.get('assignee', '')})" for a in ext["action_items"]
            ))
        if ext.get("open_questions"):
            parts.append(f"[{topic}] Open questions: " + "; ".join(q.get("question", "") for q in ext["open_questions"]))

    context = "\n\n".join(parts) if parts else full_text[:3000]

    prompt = f"""Summarize this team chat in under {max_words} words. Focus on: key decisions, who is doing what, open questions, and any blockers. Be concise and actionable.

Context:
{context}

Write a clear, readable summary (no bullet points):"""

    try:
        response = client.chat.complete(
            model="mistral-small-2409",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=500,
        )
        content = response.choices[0].message.content or ""
        logger.info("Summary generated, %d chars", len(content))
        return content.strip()
    except Exception as e:
        logger.exception("Summary generation failed: %s", e)
        return ""
