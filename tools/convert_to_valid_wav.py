from __future__ import annotations

import sys
from pathlib import Path
from typing import NoReturn

import numpy as np
import soundfile as sf


def _exit_error(message: str, *, code: int = 2) -> NoReturn:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(code)


def _downmix_to_mono(samples: np.ndarray) -> np.ndarray:
    if samples.ndim == 1:
        return samples
    if samples.ndim != 2:
        _exit_error(f"Unsupported audio array shape: {samples.shape}")
    if samples.shape[1] == 1:
        return samples[:, 0]
    if samples.shape[1] == 2:
        return (samples[:, 0] + samples[:, 1]) / 2.0
    _exit_error("Only mono or stereo WAV inputs are supported")


def _linear_resample_mono(samples: np.ndarray, *, src_sr: int, dst_sr: int) -> np.ndarray:
    if src_sr == dst_sr:
        return samples

    if samples.size == 0:
        return samples

    duration_s = samples.shape[0] / float(src_sr)
    dst_len = int(round(duration_s * dst_sr))
    if dst_len <= 0:
        return np.zeros((0,), dtype=samples.dtype)

    src_x = np.linspace(0.0, duration_s, num=samples.shape[0], endpoint=False, dtype=np.float64)
    dst_x = np.linspace(0.0, duration_s, num=dst_len, endpoint=False, dtype=np.float64)
    out = np.interp(dst_x, src_x, samples.astype(np.float64)).astype(np.float32)
    return out


def convert_to_pcm16_mono_16k(in_path: Path, out_path: Path) -> None:
    try:
        data, sr = sf.read(str(in_path), dtype="float32", always_2d=True)
    except Exception as exc:  # noqa: BLE001
        _exit_error(f"Failed to read WAV: {exc}")

    mono = _downmix_to_mono(data)
    mono_16k = _linear_resample_mono(mono, src_sr=int(sr), dst_sr=16_000)

    mono_16k = np.clip(mono_16k, -1.0, 1.0)
    pcm16 = (mono_16k * 32767.0).round().astype(np.int16)

    try:
        sf.write(str(out_path), pcm16, 16_000, subtype="PCM_16", format="WAV")
    except Exception as exc:  # noqa: BLE001
        _exit_error(f"Failed to write output WAV: {exc}")


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("Usage: python tools/convert_to_valid_wav.py input.wav output.wav", file=sys.stderr)
        return 2

    in_path = Path(argv[1]).expanduser().resolve()
    out_path = Path(argv[2]).expanduser().resolve()

    if not in_path.exists() or not in_path.is_file():
        _exit_error(f"Input file not found: {in_path}")

    if in_path.suffix.lower() != ".wav":
        _exit_error("Input must be a .wav file")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    convert_to_pcm16_mono_16k(in_path, out_path)

    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
