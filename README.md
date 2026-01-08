# VoiceForge AI

VoiceForge AI is a production-grade **voice intelligence system** that turns speech into real-time transcripts and structured “what should we do next?” intelligence.

It’s designed as a senior-engineering portfolio project: a clean FastAPI backend with a streaming WebSocket protocol, a modular speech → intelligence pipeline, and an Android-first Flutter client that sends raw PCM audio and renders live results.

## What it does

- **Audio input**
  - Upload an audio file (`POST /transcribe`)
  - Stream raw PCM16 audio over WebSocket (`WS /stream/transcribe`)
- **Voice pipeline**
  - Decode audio → PCM16 mono 16kHz
  - Voice Activity Detection (WebRTC VAD)
  - Speech-to-Text (Groq speech models)
  - Transcript post-processing (cleanup, normalization)
  - LLM reasoning (Groq LLM)
- **Output**
  - Raw transcript
  - Clean transcript
  - Strict **structured JSON intelligence** (summary, intent, action items, entities, topics)

## Architecture

High level:

- **Flutter app** records microphone audio as **PCM16 mono 16kHz** and streams frames to the backend over WebSocket.
- **FastAPI backend** micro-batches audio, runs STT (Groq Whisper), cleans transcripts, and (optionally) runs an LLM step to generate structured JSON intelligence.

Detailed docs:

- `docs/architecture.md`
- `docs/api.md`

## Repository structure

```
voiceforge-ai/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── speech/
│   │   ├── llm/
│   │   ├── pipeline/
│   │   ├── services/
│   │   ├── schemas/
│   │   └── config/
│   ├── main.py
│   └── requirements.txt
├── docs/
│   ├── architecture.md
│   └── api.md
├── README.md
└── LICENSE
```

## Setup

### 1) Create a virtual environment (Python 3.11+)

### 2) Install dependencies

From `voiceforge-ai/backend`:

```bash
pip install -r requirements.txt
```

### 3) Configure environment variables

You must provide a Groq API key:

- `GROQ_API_KEY`

Optional:
- `GROQ_BASE_URL` (default: `https://api.groq.com/openai/v1`)
- `GROQ_STT_MODEL` (default: `whisper-large-v3`)
- `GROQ_LLM_MODEL` (default: `llama-3.3-70b-versatile`)

### 4) Run the server

From `voiceforge-ai/backend`:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Open:
- Swagger UI: `http://localhost:8000/docs`

Endpoints:

- `POST /transcribe` (upload file)
- `WS /stream/transcribe` (real-time PCM streaming)

## API examples

### Transcribe + analyze an uploaded audio file

Request:

```bash
curl -X POST "http://localhost:8000/transcribe" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample.wav"
```

Response (shape):

```json
{
  "transcription": {
    "raw_transcript": "...",
    "clean_transcript": "...",
    "segments": [{"start_s": null, "end_s": null, "text": "..."}]
  },
  "intelligence": {
    "summary": "...",
    "intent": "...",
    "action_items": [{"description": "...", "owner": null, "due_date": null, "priority": null}],
    "entities": [{"type": "person", "value": "...", "confidence": 0.86}],
    "sentiment": null,
    "topics": []
  }
}
```

### Analyze an existing transcript

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"transcript":"We should ship on Friday. Ahmad will update the deck."}'
```

### Stream transcription over WebSocket

The WebSocket endpoint accepts **binary PCM16LE mono frames**.

- Connect: `ws://localhost:8000/stream/transcribe`
- Send binary audio frames continuously.
- Send a text message: `{ "event": "flush" }` to force a final transcript + intelligence.

## Creating a valid test WAV (ffmpeg-free)

For local development and Swagger testing, the backend intentionally accepts **WAV PCM16 mono 16kHz only**.

A developer utility is included to convert common voice-note WAVs into a compliant file (no ffmpeg required):

```bash
python tools/convert_to_valid_wav.py input.wav output_16k_mono_pcm16.wav
```

This script is a developer tool for generating test fixtures. It is not intended to be production-grade audio ingestion.

## Operational notes

- **Audio decoding modes** are controlled via `AUDIO_DECODER_MODE=auto|strict|universal`.
- `auto` (default): prefers ffmpeg-backed decoding when available, otherwise falls back to strict WAV.
- `strict`: WAV-only (PCM16 mono 16kHz).
- `universal`: requires ffmpeg and supports common formats (wav, mp3, m4a, ogg, opus, webm).
- The WebSocket streaming mode is implemented as a low-latency *micro-batch* transcriber.
- Groq is encapsulated in `backend/app/services/groq.py` to support future providers (OpenAI, local models) without rewriting the pipeline.

## Flutter demo app (minimal client)

The repository includes a minimal Android-first Flutter client in `voiceforge-app/`:

- Press-and-hold microphone recording
- Streams PCM16 mono 16kHz to `WS /stream/transcribe`
- Renders live transcript and final intelligence

To run it:

```bash
cd voiceforge-app
flutter pub get
flutter run
```

Backend URL notes:

- Android emulator: use `ws://10.0.2.2:8000/stream/transcribe`
- Physical device: use your machine LAN IP, e.g. `ws://192.168.1.10:8000/stream/transcribe`

## Known limitations

- Android `minSdkVersion` is **24**.
- `AUDIO_DECODER_MODE=universal` requires **ffmpeg** available on the server host.

## License

MIT — see `LICENSE`.
