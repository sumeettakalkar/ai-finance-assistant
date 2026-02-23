"""Audio transcription via OpenAI Whisper API."""

from __future__ import annotations

import io
from typing import Optional

from openai import OpenAI


def transcribe_audio(
    audio_bytes: bytes,
    model: str = "whisper-1",
    language: str = "en",
) -> Optional[str]:
    """Transcribe audio bytes using OpenAI Whisper.

    Parameters
    ----------
    audio_bytes : bytes
        Raw audio data (WAV, MP3, etc.).
    model : str
        Whisper model to use (default "whisper-1").
    language : str
        Language hint (default "en").

    Returns
    -------
    str or None
        Transcribed text, or None on failure.
    """
    try:
        client = OpenAI()
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "recording.wav"

        transcript = client.audio.transcriptions.create(
            model=model,
            file=audio_file,
            language=language,
        )
        text = transcript.text.strip()
        return text if text else None
    except Exception as e:
        print(f"Whisper transcription failed: {e}")
        return None
