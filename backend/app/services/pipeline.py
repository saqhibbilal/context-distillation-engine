"""Orchestrates embedding, vector storage, clustering, noise filtering, and extraction."""

import logging
import os
from typing import Any

from app.models.message import Message

logger = logging.getLogger(__name__)

from .clustering import cluster_embeddings, get_cluster_summary
from .embeddings import embed_messages
from .extraction import extract_from_cluster
from .noise_filter import compute_noise_scores, filter_low_signal
from .summary import generate_summary
from .vector_store import store_embeddings


def _format_messages_for_extraction(messages: list[dict]) -> str:
    """Format message list as text for LLM."""
    lines = []
    for m in messages:
        author = m.get("author", "Unknown")
        content = m.get("content", "")
        ts = m.get("timestamp", "")
        if ts:
            lines.append(f"[{ts}] {author}: {content}")
        else:
            lines.append(f"{author}: {content}")
    return "\n".join(lines)


def process_session(session_id: str, messages: list[Message]) -> dict[str, Any]:
    """
    Run the full pipeline: embed -> ChromaDB -> cluster -> noise filter -> Mistral extraction.
    Returns processed result for API response.
    """
    if not messages:
        return {
            "session_id": session_id,
            "message_count": 0,
            "clusters": [],
            "noise_scores": [],
            "extractions": [],
        }

    # Embed
    embeddings = embed_messages(messages)

    # Store in ChromaDB
    store_embeddings(session_id, messages, embeddings)

    # Cluster
    labels = cluster_embeddings(embeddings, min_cluster_size=2, min_samples=1)

    # Noise scores
    noise_scores = compute_noise_scores(messages)

    # Build cluster summaries (before filtering for full view)
    msg_dicts = [m.model_dump(mode="json") for m in messages]
    clusters_raw = get_cluster_summary(labels, msg_dicts)

    # Apply noise filter
    clusters = filter_low_signal(clusters_raw, messages, noise_scores, threshold=0.7)

    # Mistral extraction per cluster (include Unclustered, min 2 messages per cluster)
    extractions: list[dict[str, Any]] = []
    summary = ""
    api_key = os.environ.get("MISTRAL_API_KEY", "").strip()
    if not api_key:
        logger.warning("MISTRAL_API_KEY not set - skipping extraction")
    else:
        clusters_for_extraction = [c for c in clusters if c["message_count"] >= 2]
        # Fallback: if no cluster has 2+ messages, run extraction on full conversation
        if not clusters_for_extraction and len(msg_dicts) >= 2:
            full_text = _format_messages_for_extraction(msg_dicts)
            if len(full_text) >= 20:
                try:
                    ext = extract_from_cluster(full_text, topic_name="Conversation")
                    extractions.append({
                        "topic_id": 0,
                        "topic_name": "Conversation",
                        "extraction": ext.model_dump(mode="json"),
                    })
                except Exception as e:
                    logger.exception("Extraction failed (full fallback): %s", e)
        for c in clusters_for_extraction:
            msg_text = _format_messages_for_extraction(c["messages"])
            if len(msg_text) < 20:
                continue
            try:
                ext = extract_from_cluster(msg_text, topic_name=c["topic_name"])
                extractions.append(
                    {
                        "topic_id": c["topic_id"],
                        "topic_name": c["topic_name"],
                        "extraction": ext.model_dump(mode="json"),
                    }
                )
            except Exception as e:
                logger.exception("Extraction failed for %s: %s", c["topic_name"], e)

        # Generate prose summary (~250 words)
        full_text = _format_messages_for_extraction(msg_dicts)
        summary = ""
        try:
            summary = generate_summary(extractions, full_text, max_words=250)
        except Exception as e:
            logger.exception("Summary generation failed: %s", e)

    return {
        "session_id": session_id,
        "message_count": len(messages),
        "clusters": clusters,
        "noise_scores": [round(s, 2) for s in noise_scores],
        "extractions": extractions,
        "summary": summary,
    }
