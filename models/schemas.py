from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class Ticket(BaseModel):
    id: str
    text: str
    customer_tier: str = "standard"
    channel: str = "email"


class Action(BaseModel):
    action_type: Literal["classify", "respond", "escalate"]
    content: str = Field(..., min_length=1)


class HistoryItem(BaseModel):
    action_type: str
    content: str
    reward: float = Field(default=0.0, ge=0.0, le=1.0)
    note: str | None = None


class State(BaseModel):
    ticket: Ticket
    history: list[HistoryItem] = Field(default_factory=list)
    step_count: int = Field(default=0, ge=0)


class StepResult(BaseModel):
    state: State
    reward: float = Field(..., ge=0.0, le=1.0)
    done: bool
    info: dict[str, Any] = Field(default_factory=dict)
