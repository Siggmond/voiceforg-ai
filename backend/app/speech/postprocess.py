from __future__ import annotations

import re


class TranscriptPostProcessor:
    _whitespace_re = re.compile(r"\s+")

    def clean(self, transcript: str) -> str:
        text = transcript.strip()
        text = self._whitespace_re.sub(" ", text)
        if text and text[-1] not in {".", "?", "!"}:
            text = f"{text}."
        return text
