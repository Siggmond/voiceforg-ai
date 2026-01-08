from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from dataclasses import dataclass

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.api.deps import get_pipeline
from app.pipeline.voice_intelligence import VoiceIntelligencePipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stream")


@dataclass
class StreamState:
    pcm16_buffer: bytearray
    last_emitted_text: str
    lock: asyncio.Lock


async def _emit(websocket: WebSocket, payload: dict) -> None:
    await websocket.send_text(json.dumps(payload))


@router.websocket("/transcribe")
async def stream_transcribe(
    websocket: WebSocket,
    pipeline: VoiceIntelligencePipeline = Depends(get_pipeline),
) -> None:
    await websocket.accept()

    client = websocket.client
    client_label = f"{client.host}:{client.port}" if client else "unknown"
    logger.info(f"WS /stream/transcribe connected ({client_label})")

    state = StreamState(pcm16_buffer=bytearray(), last_emitted_text="", lock=asyncio.Lock())

    await _emit(
        websocket,
        {
            "event": "ready",
            "input": {
                "format": "pcm16",
                "sample_rate_hz": pipeline.sample_rate_hz,
                "channels": 1,
            },
            "protocol": {
                "binary": "Send raw PCM16LE mono frames as binary WebSocket messages.",
                "text": "Send {\"event\":\"flush\"} to force finalize and emit intelligence.",
            },
        },
    )

    async def transcribe_loop() -> None:
        while True:
            try:
                await asyncio.sleep(1.0)
                async with state.lock:
                    if len(state.pcm16_buffer) < pipeline.sample_rate_hz * 2:
                        continue
                    pcm = bytes(state.pcm16_buffer)
                    state.pcm16_buffer.clear()

                try:
                    tr = await pipeline.transcribe_pcm16(pcm16=pcm)
                except Exception as e:
                    logger.warning(f"WS transcribe failed ({client_label}): {e}")
                    continue

                if not tr.clean_transcript:
                    continue

                delta = tr.clean_transcript
                if state.last_emitted_text and delta.startswith(state.last_emitted_text):
                    delta = delta[len(state.last_emitted_text) :].lstrip()

                state.last_emitted_text = tr.clean_transcript

                try:
                    await _emit(
                        websocket,
                        {
                            "event": "partial_transcript",
                            "raw_transcript": tr.raw_transcript,
                            "clean_transcript": tr.clean_transcript,
                            "delta": delta,
                        },
                    )
                except Exception as e:
                    logger.warning(f"WS emit partial failed ({client_label}): {e}")
                    return
            except asyncio.CancelledError:
                return
            except Exception as e:
                logger.warning(f"WS background loop error ({client_label}): {e}")
                continue

    task = asyncio.create_task(transcribe_loop())

    try:
        while True:
            try:
                message = await websocket.receive()
            except Exception as e:
                logger.warning(f"WS receive failed ({client_label}): {e}")
                break
            if message.get("type") == "websocket.disconnect":
                raise WebSocketDisconnect

            if "bytes" in message and message["bytes"] is not None:
                chunk: bytes = message["bytes"]
                if chunk:
                    async with state.lock:
                        state.pcm16_buffer.extend(chunk)

            if "text" in message and message["text"] is not None:
                text = message["text"]
                try:
                    evt = json.loads(text)
                except json.JSONDecodeError:
                    continue

                if evt.get("event") == "flush":
                    logger.info(f"WS flush received ({client_label})")
                    async with state.lock:
                        pcm = bytes(state.pcm16_buffer)
                        state.pcm16_buffer.clear()

                    tr = None
                    if pcm:
                        try:
                            tr = await pipeline.transcribe_pcm16(pcm16=pcm)
                        except Exception as e:
                            logger.warning(f"WS flush transcribe failed ({client_label}): {e}")
                            tr = None
                    clean = tr.clean_transcript if tr else state.last_emitted_text
                    intelligence = None
                    if clean:
                        try:
                            intelligence = await pipeline.reasoner.analyze(transcript=clean)
                        except Exception as e:
                            logger.warning(f"WS LLM analyze failed ({client_label}): {e}")
                            intelligence = None

                    try:
                        await _emit(
                            websocket,
                            {
                                "event": "final",
                                "raw_transcript": tr.raw_transcript if tr else "",
                                "clean_transcript": clean,
                                "intelligence": intelligence.model_dump() if intelligence else None,
                            },
                        )
                    except Exception as e:
                        logger.warning(f"WS emit final failed ({client_label}): {e}")
                        break

    except WebSocketDisconnect:
        logger.info(f"WS /stream/transcribe disconnected ({client_label})")
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

        logger.info(f"WS /stream/transcribe closed ({client_label})")
