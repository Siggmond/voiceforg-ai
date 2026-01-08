from __future__ import annotations

from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    description: str
    owner: str | None = None
    due_date: str | None = None
    priority: str | None = None


class Entity(BaseModel):
    type: str = Field(..., description="Entity type: person, org, product, date, location, etc")
    value: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class IntelligenceResult(BaseModel):
    summary: str
    intent: str | None = None
    action_items: list[ActionItem] = Field(default_factory=list)
    entities: list[Entity] = Field(default_factory=list)
    sentiment: str | None = None
    topics: list[str] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    transcript: str


class AnalyzeResponse(BaseModel):
    raw_transcript: str | None = None
    clean_transcript: str | None = None
    intelligence: IntelligenceResult
