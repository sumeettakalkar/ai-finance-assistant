"""Audio input component using Whisper transcription."""

from __future__ import annotations

import hashlib
from typing import Optional

import streamlit as st


def render_audio_input(key: str = "audio") -> Optional[str]:
    """Render a microphone button and return transcribed text.

    Uses the audio-recorder-streamlit component to capture audio,
    then sends it to OpenAI Whisper for transcription.

    Returns transcribed text only once per unique recording — subsequent
    reruns with the same audio bytes are ignored to prevent infinite loops.

    Parameters
    ----------
    key : str
        Unique key for the Streamlit widget.

    Returns
    -------
    str or None
        Transcribed text, or None if no audio recorded or already processed.
    """
    try:
        from audio_recorder_streamlit import audio_recorder
    except ImportError:
        st.caption("Audio input requires: `pip install audio-recorder-streamlit`")
        return None

    audio_bytes = audio_recorder(
        text="Click to record",
        recording_color="#EF553B",
        neutral_color="#636EFA",
        icon_size="2x",
        key=f"audio_recorder_{key}",
    )

    if audio_bytes is None:
        return None

    # Deduplicate: skip if we already processed this exact recording.
    audio_hash = hashlib.md5(audio_bytes).hexdigest()
    state_key = f"_audio_processed_{key}"

    if st.session_state.get(state_key) == audio_hash:
        return None

    text = _transcribe(audio_bytes)
    if text:
        # Mark as processed so the next rerun won't re-transcribe.
        st.session_state[state_key] = audio_hash
    return text


def _transcribe(audio_bytes: bytes) -> Optional[str]:
    """Transcribe audio using OpenAI Whisper API."""
    try:
        from src.tools.audio_tools import transcribe_audio
        text = transcribe_audio(audio_bytes)
        if text:
            st.info(f"Transcribed: {text}")
        return text
    except ImportError:
        st.error("Audio transcription module not available.")
        return None
    except Exception as e:
        st.error(f"Transcription error: {e}")
        return None
