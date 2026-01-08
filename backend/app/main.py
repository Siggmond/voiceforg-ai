from __future__ import annotations

import contextlib
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.api.router import api_router
from app.config.logging import configure_logging
from app.config.settings import get_settings
from app.llm.reasoner import IntelligenceReasoner
from app.pipeline.voice_intelligence import VoiceIntelligencePipeline
from app.services.groq import GroqClient
from app.services.http import build_async_http_client
from app.speech.decoders import build_decoder
from app.speech.postprocess import TranscriptPostProcessor
from app.speech.vad import VADConfig, VoiceActivityDetector

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI):
        http = build_async_http_client(settings)
        groq = GroqClient(settings=settings, http=http)
        decoder = build_decoder(mode=settings.audio_decoder_mode, sample_rate_hz=settings.audio_sample_rate_hz)
        logger.info(
            f"Audio decoder mode={settings.audio_decoder_mode} sample_rate_hz={settings.audio_sample_rate_hz}"
        )
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

        app.state.http = http
        app.state.pipeline = VoiceIntelligencePipeline(
            groq=groq,
            decoder=decoder,
            vad=vad,
            post=post,
            reasoner=reasoner,
            sample_rate_hz=settings.audio_sample_rate_hz,
        )

        try:
            yield
        finally:
            await http.aclose()

    application = FastAPI(
        title=settings.app_name,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router)

    return application
