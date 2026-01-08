from __future__ import annotations

from dataclasses import dataclass

import webrtcvad

from app.speech.audio import frame_generator


@dataclass(frozen=True)
class VADConfig:
    aggressiveness: int
    sample_rate_hz: int
    frame_ms: int
    padding_ms: int


class VoiceActivityDetector:
    def __init__(self, *, config: VADConfig) -> None:
        self._cfg = config
        self._vad = webrtcvad.Vad(self._cfg.aggressiveness)

    def segment(self, pcm16: bytes) -> list[bytes]:
        frames = frame_generator(pcm16, sample_rate_hz=self._cfg.sample_rate_hz, frame_ms=self._cfg.frame_ms)
        if not frames:
            return []

        num_padding_frames = max(1, int(self._cfg.padding_ms / self._cfg.frame_ms))

        segments: list[bytes] = []
        ring: list[tuple[bytes, bool]] = []
        triggered = False
        voiced: list[bytes] = []

        for frame in frames:
            is_speech = self._vad.is_speech(frame, self._cfg.sample_rate_hz)

            if not triggered:
                ring.append((frame, is_speech))
                if len(ring) > num_padding_frames:
                    ring.pop(0)

                num_voiced = sum(1 for _, speech in ring if speech)
                if num_voiced > 0.9 * len(ring):
                    triggered = True
                    voiced.extend(f for f, _ in ring)
                    ring.clear()
            else:
                voiced.append(frame)
                ring.append((frame, is_speech))
                if len(ring) > num_padding_frames:
                    ring.pop(0)

                num_unvoiced = sum(1 for _, speech in ring if not speech)
                if num_unvoiced > 0.9 * len(ring):
                    segments.append(b"".join(voiced))
                    voiced = []
                    ring.clear()
                    triggered = False

        if voiced:
            segments.append(b"".join(voiced))

        return segments
