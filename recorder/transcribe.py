"""Local transcription with faster-whisper (Whisper tiny by default).

No network call is made by this module itself. The first run downloads the
Whisper model (~75 MB for tiny) from Hugging Face into the standard cache
and reuses it afterwards. Everything runs on CPU.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

from .transcript import Transcript

_MODEL_CACHE: dict[str, object] = {}


def check_ffmpeg() -> str:
    """Return the ffmpeg path or raise a clear error."""
    path = shutil.which("ffmpeg")
    if not path:
        raise RuntimeError(
            "ffmpeg was not found on PATH. Install it first "
            "(https://ffmpeg.org/download.html) — audio extraction and "
            "video cutting both need it."
        )
    return path


def probe_duration(video_path: str) -> float:
    """Media duration in seconds via ffprobe (0.0 if it cannot be read)."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return 0.0
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", video_path],
        capture_output=True, text=True, timeout=60,
    )
    try:
        return float(result.stdout.strip())
    except (ValueError, TypeError):
        return 0.0


def extract_audio(video_path: str, wav_path: str) -> None:
    """Extract 16 kHz mono WAV audio from a video file with ffmpeg."""
    check_ffmpeg()
    result = subprocess.run(
        [shutil.which("ffmpeg"), "-y", "-v", "error", "-i", video_path,
         "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", wav_path],
        capture_output=True, text=True, timeout=600,
    )
    if result.returncode != 0 or not os.path.exists(wav_path):
        raise RuntimeError(
            f"ffmpeg could not extract audio from {video_path!r}: "
            f"{result.stderr.strip() or 'unknown error'}"
        )


def _load_model(model_name: str):
    if model_name not in _MODEL_CACHE:
        from faster_whisper import WhisperModel
        _MODEL_CACHE[model_name] = WhisperModel(
            model_name, device="cpu", compute_type="int8")
    return _MODEL_CACHE[model_name]


def transcribe(video_path: str, model_name: str = "tiny",
               language: str | None = None) -> Transcript:
    """Transcribe a video/audio file locally. Returns a word-level Transcript."""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"no such file: {video_path}")
    duration = probe_duration(video_path)
    with tempfile.TemporaryDirectory(prefix="recorder-audio-") as tmp:
        wav_path = os.path.join(tmp, "audio.wav")
        extract_audio(video_path, wav_path)
        model = _load_model(model_name)
        segments, info = model.transcribe(
            wav_path, word_timestamps=True,
            language=language or None,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
        )
        segments = list(segments)
        transcript = Transcript.from_whisper(
            segments, source=os.path.basename(video_path),
            model=model_name, language=info.language or "")
    if duration:
        transcript.duration = max(transcript.duration, duration)
    return transcript
