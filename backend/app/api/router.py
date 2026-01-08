from __future__ import annotations

from fastapi import APIRouter

from app.api.routes.analyze import router as analyze_router
from app.api.routes.transcribe import router as transcribe_router
from app.api.routes.stream import router as stream_router

api_router = APIRouter()

api_router.include_router(transcribe_router, tags=["speech"])
api_router.include_router(stream_router, tags=["speech"])
api_router.include_router(analyze_router, tags=["intelligence"])
