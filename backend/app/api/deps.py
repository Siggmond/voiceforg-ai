from __future__ import annotations

from starlette.requests import HTTPConnection

from app.pipeline.voice_intelligence import VoiceIntelligencePipeline


def get_pipeline(request: HTTPConnection) -> VoiceIntelligencePipeline:
    pipeline = getattr(request.app.state, "pipeline", None)
    if pipeline is None:
        raise RuntimeError("Pipeline not initialized")
    return pipeline
