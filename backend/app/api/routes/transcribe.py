from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.deps import get_pipeline
from app.pipeline.voice_intelligence import VoiceIntelligencePipeline
from app.schemas.transcription import TranscribeResponse
from app.speech.audio import AudioDecodingError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transcribe")


@router.post("", response_model=TranscribeResponse)
async def transcribe(
    file: UploadFile = File(...),
    pipeline: VoiceIntelligencePipeline = Depends(get_pipeline),
) -> TranscribeResponse:
    filename = file.filename or "audio"
    audio_bytes = await file.read()
    try:
        transcription, intelligence = await pipeline.transcribe_and_analyze_file(
            audio_bytes=audio_bytes,
            filename=filename,
        )
    except AudioDecodingError as exc:
        raise HTTPException(status_code=400, detail=str(exc) or "Invalid or unsupported audio") from exc
    except Exception as exc:
        logger.warning(f"POST /transcribe failed for {filename}: {exc}")
        raise HTTPException(status_code=500, detail="Transcription failed") from exc

    return TranscribeResponse(transcription=transcription, intelligence=intelligence)
