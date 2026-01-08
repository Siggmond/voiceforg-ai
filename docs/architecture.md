# Architecture

## Overview

VoiceForge AI is a voice intelligence backend designed around an explicit, auditable pipeline:

1. **Ingestion**
2. **Normalization** (decode/convert)
3. **Segmentation** (VAD)
4. **Speech-to-Text** (Groq)
5. **Transcript post-processing**
6. **LLM reasoning** (Groq)
7. **Structured JSON output**

The system is built with an async-first FastAPI backend, with provider logic isolated behind service classes.

## Key modules

- `backend/app/config/`
  - Environment-variable driven configuration (`pydantic-settings`)
  - Centralized logging setup

- `backend/app/services/`
  - HTTP client construction
  - Groq integration (speech + LLM)[js-compatible OpenAI-style endpoints]

- `backend/app/speech/`
  - Audio decoding and WAV/PCM conversion
  - Voice Activity Detection (WebRTC VAD)
  - Transcript cleanup

- `backend/app/llm/`
  - JSON-first reasoning layer and schema validation

- `backend/app/pipeline/`
  - High-level orchestration (`VoiceIntelligencePipeline`)

- `backend/app/api/`
  - REST + WebSocket API routers

## Data flow

### File upload path (`POST /transcribe`)

- Receive audio file (multipart)
- Decode to PCM16 mono 16kHz
- Run VAD to produce voiced segments
- Transcribe each voiced segment via Groq speech endpoint
- Join segments into a single transcript
- Post-process into `clean_transcript`
- Run LLM analysis and validate output schema

### Streaming path (`WS /stream/transcribe`)

- Client streams PCM16 mono frames as binary WS messages
- Server micro-batches buffered audio every ~1s
- Each batch goes through the same VAD + STT + post-processing
- Server emits incremental transcript events
- Client can send `{ "event": "flush" }` to force a final transcript and intelligence extraction

## Reliability and correctness

- **Retries**: Groq network calls use bounded exponential backoff.
- **Schema enforcement**: The reasoning output is validated via Pydantic models; invalid outputs fail fast.
- **Resource lifecycle**: The FastAPI lifespan initializes a shared `httpx.AsyncClient` and closes it on shutdown.

## Extensibility

- Replace Groq by implementing an alternative provider in `backend/app/services/` and wiring it into the pipeline.
- Add persistence (Postgres) by introducing a repository layer and storing transcripts/intelligence artifacts.
- Add observability by adding OpenTelemetry tracing and structured logging correlators.
