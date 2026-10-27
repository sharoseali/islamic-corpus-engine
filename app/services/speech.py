"""Speech-to-text for voice search.

Runs Whisper locally (faster-whisper, CPU int8) so voice search works in
every browser, including those without a built-in speech engine such as
Firefox, and no audio leaves the server. The model loads lazily on the
first request and is then reused.
"""

import shutil
import subprocess
import threading

import numpy as np

from app.core.config import get_settings

# Short, domain-specific hints steer spelling of religious vocabulary in
# the chosen language without changing what the user said.
_PROMPTS = {
    "ur": "قرآن، حدیث، تفسیر، دعا، صبر، شفا، نماز۔",
    "ar": "القرآن، الحديث، التفسير، الدعاء، الصبر، الشفاء.",
    "en": "Quran, Hadith, Tafsir, dua, patience, healing.",
}

_model = None
_lock = threading.Lock()


class SpeechUnavailable(RuntimeError):
    """The speech engine (faster-whisper) is not installed on this server."""


def _get_model():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                try:
                    from faster_whisper import WhisperModel
                except ImportError as exc:
                    raise SpeechUnavailable("faster-whisper is not installed") from exc

                settings = get_settings()
                _model = WhisperModel(
                    settings.WHISPER_MODEL,
                    device=settings.WHISPER_DEVICE,
                    compute_type=settings.WHISPER_COMPUTE_TYPE,
                )
    return _model


def _decode(audio: bytes) -> np.ndarray:
    """Decode any browser recording to 16 kHz mono float32 with ffmpeg.

    Used instead of faster-whisper's PyAV decoder, whose API varies across
    PyAV releases; ffmpeg reads every format browsers record in.
    """
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SpeechUnavailable("ffmpeg is not installed")
    result = subprocess.run(
        [ffmpeg, "-nostdin", "-loglevel", "error", "-i", "pipe:0",
         "-f", "f32le", "-ac", "1", "-ar", "16000", "pipe:1"],
        input=audio,
        capture_output=True,
        timeout=60,
        check=True,
    )
    return np.frombuffer(result.stdout, dtype=np.float32)


def transcribe(audio: bytes, lang: str) -> str:
    """Transcribe a short recorded clip (webm/ogg/mp4/wav) in `lang`."""
    segments, _info = _get_model().transcribe(
        _decode(audio),
        language=lang,
        task="transcribe",
        beam_size=5,
        vad_filter=True,
        initial_prompt=_PROMPTS.get(lang),
        condition_on_previous_text=False,
    )
    return " ".join(seg.text.strip() for seg in segments).strip()
