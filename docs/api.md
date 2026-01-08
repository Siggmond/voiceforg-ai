# API

Base URL (local): `http://localhost:8000`

## REST

### `POST /transcribe`

Upload an audio file and get:
- Raw transcript
- Clean transcript
- Structured intelligence JSON

Supported formats depend on `AUDIO_DECODER_MODE`:
- `auto`/`universal`: wav, mp3, m4a, ogg, opus, webm (ffmpeg-backed)
- `strict`: WAV PCM16 mono 16kHz only

**Request**
- Content-Type: `multipart/form-data`
- Field: `file`

**Response**: `200 OK`

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
    "action_items": [],
    "entities": [],
    "sentiment": null,
    "topics": []
  }
}
```

### `POST /analyze`

Analyze a transcript string (no audio).

**Request**

```json
{
  "transcript": "We should ship on Friday. Ahmad will update the deck."
}
```

**Response**

```json
{
  "raw_transcript": "...",
  "clean_transcript": "...",
  "intelligence": {
    "summary": "...",
    "intent": "...",
    "action_items": [],
    "entities": [],
    "sentiment": null,
    "topics": []
  }
}
```

## WebSocket

### `WS /stream/transcribe`

**Protocol**

- Connect and wait for a `ready` JSON event.
- Send audio as **binary** messages:
  - format: PCM16LE
  - channels: 1
  - sample rate: 16kHz
- To finalize:
  - send a **text** message: `{ "event": "flush" }`

**Server events**

- `ready`
- `partial_transcript`
- `final`

**Example partial event**

```json
{
  "event": "partial_transcript",
  "raw_transcript": "...",
  "clean_transcript": "...",
  "delta": "..."
}
```

**Example final event**

```json
{
  "event": "final",
  "raw_transcript": "...",
  "clean_transcript": "...",
  "intelligence": {
    "summary": "...",
    "intent": "...",
    "action_items": [],
    "entities": [],
    "sentiment": null,
    "topics": []
  }
}
```
