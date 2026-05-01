"""Design decisions — LLM-generated questions answered by the user before prompt build."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DecisionOption(BaseModel):
    id: str
    label: str
    description: str = ""


class DesignDecision(BaseModel):
    id: str
    question: str
    options: list[DecisionOption] = Field(default_factory=list)
    allow_freeform: bool = False
    rationale: str = ""


class DecisionAnswer(BaseModel):
    decision_id: str
    selected_option_id: str | None = None
    freeform_answer: str | None = None
