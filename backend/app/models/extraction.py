"""Structured extraction models for Mistral API."""

from typing import Optional

from pydantic import BaseModel, Field


class Decision(BaseModel):
    """A key decision made in the conversation."""

    description: str = Field(..., description="What was decided")
    context: Optional[str] = Field(None, description="Brief context")
    participants: list[str] = Field(default_factory=list, description="Who was involved")


class ActionItem(BaseModel):
    """A concrete task or action to be done."""

    task: str = Field(..., description="What needs to be done")
    assignee: Optional[str] = Field(None, description="Who is responsible")
    due_context: Optional[str] = Field(None, description="Timeline or due info if mentioned")


class Responsibility(BaseModel):
    """A responsibility assigned to someone."""

    person: str = Field(..., description="Who is responsible")
    responsibility: str = Field(..., description="What they are responsible for")


class OpenQuestion(BaseModel):
    """An open question that needs an answer."""

    question: str = Field(..., description="The question")
    context: Optional[str] = Field(None, description="Why it matters")


class CriticalNote(BaseModel):
    """A critical project note or blocker."""

    note: str = Field(..., description="The note")
    category: Optional[str] = Field(None, description="e.g. blocker, risk, dependency")


class ClusterExtraction(BaseModel):
    """Extracted intelligence from a topic cluster."""

    decisions: list[Decision] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    responsibilities: list[Responsibility] = Field(default_factory=list)
    open_questions: list[OpenQuestion] = Field(default_factory=list)
    critical_notes: list[CriticalNote] = Field(default_factory=list)
    summary: Optional[str] = Field(None, description="Brief topic summary")
