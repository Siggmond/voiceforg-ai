from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "VoiceForge AI"
    environment: Literal["local", "staging", "production"] = "local"
    log_level: str = "INFO"

    cors_allow_origins: list[str] = ["*"]

    groq_api_key: SecretStr
    groq_base_url: AnyHttpUrl = "https://api.groq.com/openai/v1"
    groq_stt_model: str = "whisper-large-v3"
    groq_llm_model: str = "llama-3.3-70b-versatile"

    audio_sample_rate_hz: int = 16_000
    audio_decoder_mode: Literal["auto", "strict", "universal"] = "auto"
    vad_aggressiveness: int = 2
    vad_frame_ms: int = 30
    vad_padding_ms: int = 300

    enable_llm_punctuation: bool = False

    http_timeout_s: float = 60.0
    llm_temperature: float = 0.2
    llm_max_tokens: int = 800


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
