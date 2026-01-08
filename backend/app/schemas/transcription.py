from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.intelligence import IntelligenceResult


class TranscriptSegment(BaseModel):
    start_s: float | None = None
    end_s: float | None = None
    text: str


class TranscriptionResult(BaseModel):
    raw_transcript: str
    clean_transcript: str
    segments: list[TranscriptSegment] = Field(default_factory=list)


class TranscribeResponse(BaseModel):
    transcription: TranscriptionResult
    intelligence: IntelligenceResult
