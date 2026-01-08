from __future__ import annotations

from dataclasses import dataclass

from app.llm.reasoner import IntelligenceReasoner
from app.schemas.intelligence import IntelligenceResult
from app.schemas.transcription import TranscriptSegment, TranscriptionResult
from app.services.groq import GroqClient
from app.speech.audio import pcm16_to_wav_bytes
from app.speech.decoders import AudioDecoder
from app.speech.postprocess import TranscriptPostProcessor
from app.speech.vad import VoiceActivityDetector


@dataclass
class VoiceIntelligencePipeline:
    groq: GroqClient
    decoder: AudioDecoder
    vad: VoiceActivityDetector
    post: TranscriptPostProcessor
    reasoner: IntelligenceReasoner
    sample_rate_hz: int

    async def transcribe_and_analyze_file(self, *, audio_bytes: bytes, filename: str) -> tuple[TranscriptionResult, IntelligenceResult]:
        pcm16 = self.decoder.decode(audio_bytes=audio_bytes, filename=filename)
        transcription = await self.transcribe_pcm16(pcm16=pcm16, filename=filename)
        intelligence = await self.reasoner.analyze(transcript=transcription.clean_transcript)
        return transcription, intelligence

    async def transcribe_pcm16(self, *, pcm16: bytes, filename: str = "audio.wav") -> TranscriptionResult:
        segments_pcm = self.vad.segment(pcm16)
        if not segments_pcm:
            segments_pcm = [pcm16]

        segment_models: list[TranscriptSegment] = []
        segment_texts: list[str] = []

        for idx, seg in enumerate(segments_pcm):
            wav = pcm16_to_wav_bytes(seg, sample_rate_hz=self.sample_rate_hz)
            result = await self.groq.transcribe_audio(wav_bytes=wav, filename=f"segment-{idx}-{filename}")

            text = (result.get("text") or "").strip()
            if text:
                segment_texts.append(text)
                segment_models.append(TranscriptSegment(text=text))

        raw_transcript = " ".join(segment_texts).strip()
        clean_transcript = self.post.clean(raw_transcript)

        return TranscriptionResult(raw_transcript=raw_transcript, clean_transcript=clean_transcript, segments=segment_models)

    async def analyze_transcript(self, *, transcript: str) -> IntelligenceResult:
        clean = self.post.clean(transcript)
        return await self.reasoner.analyze(transcript=clean)
