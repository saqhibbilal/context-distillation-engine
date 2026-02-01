"""Mistral API extraction for decisions, action items, and project intelligence."""

import json
import logging
import os

from app.models.extraction import ClusterExtraction

logger = logging.getLogger(__name__)


def _get_client():
    from mistralai import Mistral

    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY environment variable is not set")
    return Mistral(api_key=api_key)


def extract_from_cluster(
    messages_text: str,
    topic_name: str = "Topic",
    model: str = "mistral-small-2409",
) -> ClusterExtraction:
    """
    Extract decisions, action items, responsibilities, and notes from a cluster of messages.
    """
    client = _get_client()

    system_prompt = """You are an expert at extracting structured project intelligence from group chat conversations.
Given a set of messages from a single topic/discussion, extract:
1. decisions: Key decisions made (description, optional context, participants involved)
2. action_items: Concrete tasks (task, optional assignee, optional due_context)
3. responsibilities: Who is responsible for what (person, responsibility)
4. open_questions: Questions raised but not yet answered (question, optional context)
5. critical_notes: Blockers, risks, dependencies (note, optional category)
6. summary: Brief 1-2 sentence topic summary

Extract only what is explicitly or clearly implied. Leave lists empty if nothing applies.
Return valid JSON matching the schema."""

    user_content = f"""Topic: {topic_name}

Messages:
{messages_text}

Extract the structured intelligence. Return JSON with keys: decisions, action_items, responsibilities, open_questions, critical_notes, summary."""

    try:
        response = client.chat.complete(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=2048,
        )
    except Exception as e:
        logger.exception("Mistral API call failed: %s", e)
        return ClusterExtraction()

    content = response.choices[0].message.content
    if not content:
        return ClusterExtraction()

    try:
        data = json.loads(content)
        return ClusterExtraction(
            decisions=[_ensure_decision(d) for d in data.get("decisions", []) if isinstance(d, dict)],
            action_items=[_ensure_action_item(a) for a in data.get("action_items", []) if isinstance(a, dict)],
            responsibilities=[_ensure_responsibility(r) for r in data.get("responsibilities", []) if isinstance(r, dict)],
            open_questions=[_ensure_open_question(q) for q in data.get("open_questions", []) if isinstance(q, dict)],
            critical_notes=[_ensure_critical_note(n) for n in data.get("critical_notes", []) if isinstance(n, dict)],
            summary=data.get("summary") if isinstance(data.get("summary"), str) else None,
        )
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("Failed to parse Mistral response: %s", e)
        return ClusterExtraction()


def _ensure_decision(d: dict):
    from app.models.extraction import Decision

    return Decision(
        description=str(d.get("description", d)),
        context=d.get("context"),
        participants=d.get("participants", []) if isinstance(d.get("participants"), list) else [],
    )


def _ensure_action_item(a: dict):
    from app.models.extraction import ActionItem

    return ActionItem(
        task=str(a.get("task", a)),
        assignee=a.get("assignee"),
        due_context=a.get("due_context"),
    )


def _ensure_responsibility(r: dict):
    from app.models.extraction import Responsibility

    return Responsibility(
        person=str(r.get("person", "")),
        responsibility=str(r.get("responsibility", r)),
    )


def _ensure_open_question(q: dict):
    from app.models.extraction import OpenQuestion

    return OpenQuestion(
        question=str(q.get("question", q)),
        context=q.get("context"),
    )


def _ensure_critical_note(n: dict):
    from app.models.extraction import CriticalNote

    return CriticalNote(
        note=str(n.get("note", n)),
        category=n.get("category"),
    )
