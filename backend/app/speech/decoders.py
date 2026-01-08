from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Literal, Protocol

from app.speech.audio import AudioDecodingError, decode_to_pcm16_mono_16k


class AudioDecoder(Protocol):
    def decode(self, *, audio_bytes: bytes, filename: str | None = None) -> bytes: ...


@dataclass(frozen=True)
class WavStrictDecoder:
    def decode(self, *, audio_bytes: bytes, filename: str | None = None) -> bytes:
        return decode_to_pcm16_mono_16k(audio_bytes)


@dataclass(frozen=True)
class UniversalDecoder:
    sample_rate_hz: int = 16_000

    def decode(self, *, audio_bytes: bytes, filename: str | None = None) -> bytes:
        try:
            from pydub import AudioSegment
        except Exception as exc:  # noqa: BLE001
            raise AudioDecodingError("Universal decoding requested but pydub is not installed") from exc

        try:
            segment = AudioSegment.from_file(
                io.BytesIO(audio_bytes),
                format=self._format_from_filename(filename),
            )
        except Exception as exc:  # noqa: BLE001
            raise AudioDecodingError(
                "Failed to decode audio. The file may be corrupted, unsupported, or ffmpeg may be missing."
            ) from exc

        segment = segment.set_channels(1).set_frame_rate(self.sample_rate_hz).set_sample_width(2)
        return segment.raw_data

    @staticmethod
    def ffmpeg_available() -> bool:
        try:
            from pydub.utils import which
        except Exception:
            return False

        return bool(which("ffmpeg") or which("ffmpeg.exe"))

    @staticmethod
    def _format_from_filename(filename: str | None) -> str | None:
        if not filename:
            return None
        if "." not in filename:
            return None
        return filename.rsplit(".", 1)[-1].lower()


DecoderMode = Literal["auto", "strict", "universal"]


def build_decoder(*, mode: DecoderMode, sample_rate_hz: int = 16_000) -> AudioDecoder:
    if mode == "strict":
        return WavStrictDecoder()

    if mode == "universal":
        if not UniversalDecoder.ffmpeg_available():
            raise AudioDecodingError("Universal decoding mode requires ffmpeg to be installed and on PATH")
        return UniversalDecoder(sample_rate_hz=sample_rate_hz)

    if UniversalDecoder.ffmpeg_available():
        return UniversalDecoder(sample_rate_hz=sample_rate_hz)

    return WavStrictDecoder()
