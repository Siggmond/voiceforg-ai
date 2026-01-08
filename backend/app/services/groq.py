from __future__ import annotations

import json
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config.settings import Settings


class GroqClient:
    def __init__(self, *, settings: Settings, http: httpx.AsyncClient) -> None:
        self._settings = settings
        self._http = http

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._settings.groq_api_key.get_secret_value()}",
        }

    @retry(wait=wait_exponential(multiplier=0.5, min=0.5, max=8), stop=stop_after_attempt(3))
    async def transcribe_audio(
        self,
        *,
        wav_bytes: bytes,
        filename: str = "audio.wav",
        prompt: str | None = None,
    ) -> dict[str, Any]:
        url = f"{self._settings.groq_base_url}/audio/transcriptions"

        data: dict[str, Any] = {
            "model": self._settings.groq_stt_model,
            "response_format": "verbose_json",
        }
        if prompt:
            data["prompt"] = prompt

        files = {
            "file": (filename, wav_bytes, "audio/wav"),
        }

        resp = await self._http.post(url, headers=self._headers, data=data, files=files)
        resp.raise_for_status()
        return resp.json()

    @retry(wait=wait_exponential(multiplier=0.5, min=0.5, max=8), stop=stop_after_attempt(3))
    async def chat_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema_hint: dict[str, Any] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        url = f"{self._settings.groq_base_url}/chat/completions"

        payload: dict[str, Any] = {
            "model": self._settings.groq_llm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature if temperature is not None else self._settings.llm_temperature,
            "max_tokens": max_tokens if max_tokens is not None else self._settings.llm_max_tokens,
            "response_format": {"type": "json_object"},
        }

        if schema_hint is not None:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": "emit_json",
                        "description": "Emit a JSON object that matches the required schema.",
                        "parameters": schema_hint,
                    },
                }
            ]
            payload["tool_choice"] = {"type": "function", "function": {"name": "emit_json"}}

        resp = await self._http.post(url, headers={**self._headers, "Content-Type": "application/json"}, content=json.dumps(payload))
        resp.raise_for_status()
        data = resp.json()

        choice = data["choices"][0]
        message = choice.get("message") or {}

        if message.get("tool_calls"):
            args = message["tool_calls"][0]["function"]["arguments"]
            return json.loads(args)

        content = message.get("content")
        if not content:
            raise RuntimeError("Groq chat completion returned empty content")
        return json.loads(content)
