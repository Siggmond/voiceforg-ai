from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.schemas.intelligence import IntelligenceResult
from app.services.groq import GroqClient


_SYSTEM_PROMPT = (
    "You are a voice intelligence engine. "
    "Return ONLY a single JSON object. No markdown. No extra keys. "
    "Be concise but precise. If unsure, use null or empty lists."
)


class IntelligenceReasoner:
    def __init__(self, *, groq: GroqClient) -> None:
        self._groq = groq

    async def analyze(self, *, transcript: str) -> IntelligenceResult:
        user_prompt = (
            "Analyze the transcript and extract structured intelligence. "
            "Return JSON with keys: summary (string), intent (string), action_items (array), entities (array), sentiment (string|null), topics (array). "
            "Action item object keys: description, owner, due_date, priority. "
            "Entity object keys: type, value, confidence (0..1 or null). "
            "Transcript:\n" + transcript
        )

        raw: dict[str, Any] = await self._groq.chat_json(system_prompt=_SYSTEM_PROMPT, user_prompt=user_prompt)
        try:
            return IntelligenceResult.model_validate(raw)
        except ValidationError as exc:
            raise RuntimeError(f"LLM returned invalid schema: {exc}") from exc
