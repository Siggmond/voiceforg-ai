from __future__ import annotations

import io
import wave
import numpy as np
import soundfile as sf


class AudioDecodingError(Exception):
    pass


def decode_to_pcm16_mono_16k(audio_bytes: bytes) -> bytes:
    bio = io.BytesIO(audio_bytes)
    try:
        info = sf.info(bio)
    except Exception as exc:  # noqa: BLE001
        raise AudioDecodingError("Only WAV PCM16 mono 16kHz files are supported") from exc

    if (info.format or "").upper() != "WAV":
        raise AudioDecodingError("Only WAV PCM16 mono 16kHz files are supported")

    if info.subtype != "PCM_16":
        raise AudioDecodingError("Only WAV PCM16 mono 16kHz files are supported")

    if info.samplerate != 16_000:
        raise AudioDecodingError("Only WAV PCM16 mono 16kHz files are supported")

    if info.channels not in (1, 2):
        raise AudioDecodingError("Only WAV PCM16 mono 16kHz files are supported")

    bio.seek(0)
    try:
        data, sr = sf.read(bio, dtype="int16", always_2d=True)
    except Exception as exc:  # noqa: BLE001
        raise AudioDecodingError("Only WAV PCM16 mono 16kHz files are supported") from exc

    if sr != 16_000:
        raise AudioDecodingError("Only WAV PCM16 mono 16kHz files are supported")

    pcm = np.asarray(data, dtype=np.int16)
    if pcm.shape[1] == 2:
        mono_i32 = (pcm[:, 0].astype(np.int32) + pcm[:, 1].astype(np.int32)) // 2
        pcm = mono_i32.astype(np.int16)[:, None]

    mono_pcm16 = np.ascontiguousarray(pcm[:, 0], dtype=np.int16)
    return mono_pcm16.tobytes()


def pcm16_to_wav_bytes(pcm16: bytes, *, sample_rate_hz: int = 16_000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate_hz)
        wf.writeframes(pcm16)
    return buf.getvalue()


def frame_generator(pcm16: bytes, *, sample_rate_hz: int, frame_ms: int) -> list[bytes]:
    bytes_per_sample = 2
    frame_len = int(sample_rate_hz * (frame_ms / 1000.0) * bytes_per_sample)
    return [pcm16[i : i + frame_len] for i in range(0, len(pcm16) - (len(pcm16) % frame_len), frame_len)]
