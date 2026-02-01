"""Noise filtering for low-signal messages."""

import re
from typing import Any

from app.models.message import Message


def _is_emoji_heavy(text: str, ratio: float = 0.5) -> bool:
    """True if a large portion of the message is emoji/unicode symbols."""
    if not text or len(text.strip()) < 3:
        return False
    # Simple heuristic: non-word, non-space chars
    stripped = text.strip()
    emoji_like = len(re.findall(r"[\U0001F300-\U0001F9FF]|[\u2600-\u26FF]|[\u2700-\u27BF]|[\U0001F600-\U0001F64F]", text))
    emoji_like += len(re.findall(r"[^\w\s.,!?;:'\"-]", text))
    return emoji_like / max(len(stripped), 1) >= ratio


def _is_very_short(text: str, min_len: int = 10) -> bool:
    """True if message is very short (likely low signal)."""
    return len(text.strip()) < min_len


def _is_likely_noise(text: str) -> bool:
    """Heuristics for common noise patterns."""
    lower = text.lower().strip()
    noise_phrases = [
        "lol",
        "lmao",
        "haha",
        "😂",
        "👍",
        "ok",
        "yeah",
        "yep",
        "nice",
        "cool",
        "same",
        "+1",
        "agreed",
        "true",
        "same here",
        "this",
        "that meme",
        "gold",
    ]
    if lower in noise_phrases or lower in ("👍", "👌", "😂", "🤣", "ok", "k"):
        return True
    if _is_very_short(text) and _is_emoji_heavy(text, 0.3):
        return True
    return False


def compute_noise_scores(messages: list[Message]) -> list[float]:
    """
    Compute a noise score per message (0 = signal, 1 = noise).
    """
    scores = []
    for m in messages:
        text = m.content.strip()
        score = 0.0
        if _is_likely_noise(text):
            score = 1.0
        elif _is_very_short(text, 15):
            score = 0.6
        elif _is_emoji_heavy(text, 0.4):
            score = 0.5
        scores.append(score)
    return scores


def filter_low_signal(
    clusters: list[dict[str, Any]],
    messages: list[Message],
    noise_scores: list[float],
    threshold: float = 0.7,
) -> list[dict[str, Any]]:
    """
    Filter out high-noise messages from clusters.
    Messages with noise_score >= threshold are marked as filtered.
    Returns clusters with filtered message indices noted.
    """
    filtered_clusters = []
    for c in clusters:
        indices = c["message_indices"]
        kept = [i for i in indices if i < len(noise_scores) and noise_scores[i] < threshold]
        filtered = [i for i in indices if i < len(noise_scores) and noise_scores[i] >= threshold]
        kept_set = set(kept)
        msg_list = [msg for idx, msg in zip(indices, c["messages"]) if idx in kept_set]
        filtered_clusters.append(
            {
                **c,
                "message_indices": kept,
                "filtered_indices": filtered,
                "message_count": len(kept),
                "filtered_count": len(filtered),
                "messages": msg_list,
            }
        )
    return filtered_clusters
