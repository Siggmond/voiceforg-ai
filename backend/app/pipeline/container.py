from __future__ import annotations

from functools import lru_cache

from app.config.settings import get_settings
from app.llm.reasoner import IntelligenceReasoner
from app.pipeline.voice_intelligence import VoiceIntelligencePipeline
from app.services.groq import GroqClient
from app.services.http import build_async_http_client
from app.speech.decoders import build_decoder
from app.speech.postprocess import TranscriptPostProcessor
from app.speech.vad import VADConfig, VoiceActivityDetector


@lru_cache(maxsize=1)
def get_pipeline() -> VoiceIntelligencePipeline:
    settings = get_settings()
    http = build_async_http_client(settings)
    groq = GroqClient(settings=settings, http=http)
    decoder = build_decoder(mode=settings.audio_decoder_mode, sample_rate_hz=settings.audio_sample_rate_hz)

    vad = VoiceActivityDetector(
        config=VADConfig(
            aggressiveness=settings.vad_aggressiveness,
            sample_rate_hz=settings.audio_sample_rate_hz,
            frame_ms=settings.vad_frame_ms,
            padding_ms=settings.vad_padding_ms,
        )
    )

    post = TranscriptPostProcessor()
    reasoner = IntelligenceReasoner(groq=groq)

    return VoiceIntelligencePipeline(
        groq=groq,
        decoder=decoder,
        vad=vad,
        post=post,
        reasoner=reasoner,
        sample_rate_hz=settings.audio_sample_rate_hz,
    )
