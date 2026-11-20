"""Cut a video by the edited transcript and export the results.

Cutting re-encodes each kept range (VP9/Opus, same codecs as the recorder
produces) so cuts land on the exact word boundaries instead of the nearest
keyframe, then joins the pieces with the ffmpeg concat demuxer.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile

from .transcribe import check_ffmpeg
from .transcript import Transcript


def _run(cmd: list[str], timeout: int = 900) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(
            "ffmpeg failed: " + (result.stderr.strip().splitlines() or [""])[-1])


def cut_video(video_path: str, keep_ranges: list[tuple[float, float]],
              output_path: str) -> str:
    """Write a new WebM containing only the kept ranges, in order."""
    if not keep_ranges:
        raise ValueError("nothing left to keep — every word was deleted")
    ffmpeg = check_ffmpeg()
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"no such file: {video_path}")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="recorder-cut-") as tmp:
        parts: list[str] = []
        for i, (start, end) in enumerate(keep_ranges):
            part = os.path.join(tmp, f"part{i:03d}.webm")
            _run([ffmpeg, "-y", "-v", "error",
                  "-ss", f"{start:.3f}", "-to", f"{end:.3f}", "-i", video_path,
                  "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "32",
                  "-c:a", "libopus", "-b:a", "96k", part])
            parts.append(part)
        if len(parts) == 1:
            shutil.copyfile(parts[0], output_path)
            return output_path
        concat_list = os.path.join(tmp, "concat.txt")
        with open(concat_list, "w", encoding="utf-8") as fh:
            for part in parts:
                fh.write(f"file '{part}'\n")
        _run([ffmpeg, "-y", "-v", "error", "-f", "concat", "-safe", "0",
              "-i", concat_list, "-c", "copy", output_path])
    return output_path


def export_all(video_path: str, transcript: Transcript, output_dir: str,
               edited_video: str = "edited.webm") -> dict[str, str]:
    """Cut the video and write edited transcript + SRT + cut report.

    Returns a dict of label -> path for everything written.
    """
    os.makedirs(output_dir, exist_ok=True)
    keep = transcript.keep_ranges()
    removed = transcript.deleted_ranges()
    outputs: dict[str, str] = {}

    video_out = os.path.join(output_dir, edited_video)
    cut_video(video_path, keep, video_out)
    outputs["edited_video"] = video_out

    retimed = transcript.retime_after_cut()
    srt_path = os.path.join(output_dir, "edited.srt")
    with open(srt_path, "w", encoding="utf-8") as fh:
        fh.write(retimed.to_srt())
    outputs["edited_srt"] = srt_path

    txt_path = os.path.join(output_dir, "edited_transcript.txt")
    with open(txt_path, "w", encoding="utf-8") as fh:
        fh.write(retimed.plain_text() + "\n")
    outputs["edited_transcript"] = txt_path

    json_path = os.path.join(output_dir, "edited_transcript.json")
    retimed.to_json(json_path)
    outputs["edited_transcript_json"] = json_path

    cuts_path = os.path.join(output_dir, "cuts.json")
    with open(cuts_path, "w", encoding="utf-8") as fh:
        json.dump({
            "source": transcript.source,
            "original_duration": round(transcript.duration, 3),
            "edited_duration": round(retimed.duration, 3),
            "words_total": len(transcript.words),
            "words_deleted": sum(1 for w in transcript.words if w.deleted),
            "removed_ranges": [[round(a, 3), round(b, 3)] for a, b in removed],
            "kept_ranges": [[round(a, 3), round(b, 3)] for a, b in keep],
        }, fh, indent=2)
    outputs["cuts_report"] = cuts_path
    return outputs
