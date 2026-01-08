# 🚀 VoiceForge AI

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![Flutter](https://img.shields.io/badge/Flutter-02569B?style=flat&logo=flutter&logoColor=white)
![Dart](https://img.shields.io/badge/Dart-0175C2?style=flat&logo=dart&logoColor=white)
![WebSocket](https://img.shields.io/badge/WebSocket-Enabled-0A66C2?style=flat)
![Android](https://img.shields.io/badge/Android-minSdk%2024-3DDC84?style=flat&logo=android&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-API-000000?style=flat)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=flat)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat)

![Stars](https://img.shields.io/github/stars/Siggmond/voiceforg-ai?style=flat)
![Last Commit](https://img.shields.io/github/last-commit/Siggmond/voiceforg-ai?style=flat)

**VoiceForge AI** is a **production-grade voice intelligence platform** that transforms raw speech into structured, actionable insights in real time.

It combines **low-latency speech-to-text**, **streaming audio ingestion**, and **LLM-powered reasoning** behind a clean API and a minimal mobile client.

This project is designed as a **serious engineering showcase**, not a demo.

---

## ✨ What VoiceForge AI Does

- 🎙️ **Live voice transcription** (streaming via WebSocket)
- 🧠 **AI reasoning** on speech:
  - summary
  - intent (nullable, schema-safe)
  - entities
  - action items
- ⚡ **Low-latency pipeline** (PCM streaming → VAD → STT → LLM)
- 📱 **Mobile app (Flutter)** for real-time testing on Android devices

---

## 🧩 Architecture Overview

```
┌──────────────┐        WebSocket (PCM16)
│ Flutter App  │ ─────────────────────────▶
└──────────────┘
                                   ┌─────────────────────────┐
                                   │ FastAPI Backend          │
                                   │                         │
                                   │ Audio Decoder            │
                                   │  ├─ strict (WAV only)   │
                                   │  └─ universal (ffmpeg)  │
                                   │                         │
                                   │ VAD (WebRTC)            │
                                   │ STT (Groq API)          │
                                   │ LLM Reasoner (JSON)     │
                                   └─────────────────────────┘
```

---

## 🛠️ Backend Features

- Modular, production-style layout
- Dual audio decoder strategy
- Configurable decoding mode
- Defensive runtime behavior
- Strict JSON validation (Pydantic v2)

---

## 📱 Mobile App (Flutter)

- Press-and-hold recording
- Streams raw PCM16 audio
- Live transcript display
- Final intelligence on release
- Clean UX with permission handling

---

## ▶️ How to Run (Local)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Swagger:
```
http://localhost:8000/docs
```

---

### Flutter App

```bash
cd voiceforge-app
flutter pub get
flutter build apk --release
flutter run --profile
```

---

## 🌐 WebSocket URLs

- Emulator:
```
ws://10.0.2.2:8000/stream/transcribe
```

- Physical device:
```
ws://<LAN-IP>:8000/stream/transcribe
```

---

## ⚙️ Environment Variables

```env
GROQ_API_KEY=your_api_key_here
AUDIO_DECODER_MODE=auto
```

---

## ⚠️ Known Limitations

- Intent may be null (schema-safe)
- Emulator audio may be unstable
- ffmpeg optional for universal decoding

---

## 🎯 Why This Project Matters

This project demonstrates:
- Real-time streaming systems
- Production-safe AI integration
- Mobile + backend coordination
- Senior-level engineering decisions

---

## 📄 License

MIT


If this project was helpful or inspiring, consider giving it a ⭐️.
