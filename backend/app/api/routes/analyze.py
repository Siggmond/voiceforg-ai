from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_pipeline
from app.pipeline.voice_intelligence import VoiceIntelligencePipeline
from app.schemas.intelligence import AnalyzeRequest, AnalyzeResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze")


@router.post("", response_model=AnalyzeResponse)
async def analyze(
    payload: AnalyzeRequest,
    pipeline: VoiceIntelligencePipeline = Depends(get_pipeline),
) -> AnalyzeResponse:
    try:
        intelligence = await pipeline.analyze_transcript(transcript=payload.transcript)
    except Exception as exc:
        logger.warning(f"POST /analyze failed: {exc}")
        raise HTTPException(status_code=500, detail="Analysis failed") from exc
    return AnalyzeResponse(
        raw_transcript=payload.transcript,
        clean_transcript=pipeline.post.clean(payload.transcript),
        intelligence=intelligence,
    )
