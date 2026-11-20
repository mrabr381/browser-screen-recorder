"""Command line interface.

Usage:
    python -m recorder transcribe recording.webm --out report/
    python -m recorder cut recording.webm transcript.json \\
        --delete-words 12,13,14 --out edited/
    python -m recorder cut recording.webm transcript.json \\
        --delete-text "um, uh" --out edited/

Exit codes: 0 ok, 1 runtime error (missing file, ffmpeg, model), 2 bad usage.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from .editor import cut_video, export_all
from .transcribe import check_ffmpeg, transcribe
from .transcript import Transcript


def _parse_indices(spec: str, total: int) -> list[int]:
    """Parse '3,5,7-9' into sorted unique 0-based word indices."""
    indices: set[int] = set()
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            start_s, _, end_s = chunk.partition("-")
            try:
                start, end = int(start_s), int(end_s)
            except ValueError:
                raise ValueError(f"bad range in --delete-words: {chunk!r}")
            if start > end or start < 0 or end >= total:
                raise ValueError(
                    f"range {chunk!r} is outside 0..{total - 1}")
            indices.update(range(start, end + 1))
        else:
            try:
                i = int(chunk)
            except ValueError:
                raise ValueError(f"bad index in --delete-words: {chunk!r}")
            if i < 0 or i >= total:
                raise ValueError(f"index {i} is outside 0..{total - 1}")
            indices.add(i)
    return sorted(indices)


def _parse_delete_text(spec: str, transcript: Transcript) -> list[int]:
    """Find word indices whose text matches any comma-separated token
    (case-insensitive, punctuation stripped)."""
    wanted = {t.strip().strip(".,!?;:\"'").lower()
              for t in spec.split(",") if t.strip()}
    return [i for i, w in enumerate(transcript.words)
            if w.text.strip(".,!?;:\"'").lower() in wanted]


def cmd_transcribe(args: argparse.Namespace) -> int:
    try:
        check_ffmpeg()
        transcript = transcribe(args.input, model_name=args.model,
                                language=args.language)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    os.makedirs(args.out, exist_ok=True)
    json_path = os.path.join(args.out, "transcript.json")
    transcript.to_json(json_path)
    srt_path = os.path.join(args.out, "transcript.srt")
    with open(srt_path, "w", encoding="utf-8") as fh:
        fh.write(transcript.to_srt())
    txt_path = os.path.join(args.out, "transcript.txt")
    with open(txt_path, "w", encoding="utf-8") as fh:
        fh.write(transcript.plain_text() + "\n")
    print(f"Transcribed {len(transcript.words)} words "
          f"({transcript.duration:.1f}s, model {transcript.model}, "
          f"lang {transcript.language or 'auto'})")
    print(f"  transcript: {json_path}")
    print(f"  subtitles:  {srt_path}")
    print(f"  text:       {txt_path}")
    return 0


def cmd_cut(args: argparse.Namespace) -> int:
    try:
        check_ffmpeg()
        transcript = Transcript.from_json(args.transcript)
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
        print(f"error: cannot read transcript {args.transcript!r}: {exc}",
              file=sys.stderr)
        return 1
    try:
        if args.delete_words:
            indices = _parse_indices(args.delete_words, len(transcript.words))
        elif args.delete_text:
            indices = _parse_delete_text(args.delete_text, transcript)
        else:
            print("error: give --delete-words or --delete-text",
                  file=sys.stderr)
            return 2
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not indices:
        print("error: nothing matched — no words selected for deletion",
              file=sys.stderr)
        return 1
    removed = transcript.delete_words(indices)
    print(f"Deleting {len(removed)} word(s): "
          + ", ".join(repr(w.text) for w in removed[:12])
          + (" …" if len(removed) > 12 else ""))
    try:
        outputs = export_all(args.input, transcript, args.out)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Edited video: {transcript.duration:.1f}s -> "
          f"{transcript.retime_after_cut().duration:.1f}s")
    for label, path in outputs.items():
        print(f"  {label}: {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="recorder",
        description="Local screen-recording transcript editor: transcribe a "
                    "WebM with local Whisper, delete words, cut the video.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_tr = sub.add_parser("transcribe", help="transcribe a recording to JSON/SRT/text")
    p_tr.add_argument("input", help="video file (WebM/MP4) to transcribe")
    p_tr.add_argument("--out", required=True, help="output directory")
    p_tr.add_argument("--model", default="tiny",
                      help="Whisper model size (default: tiny)")
    p_tr.add_argument("--language", default=None,
                      help="language code, e.g. en (default: auto-detect)")
    p_tr.set_defaults(func=cmd_transcribe)

    p_cut = sub.add_parser("cut", help="delete words and cut the video")
    p_cut.add_argument("input", help="original video file")
    p_cut.add_argument("transcript", help="transcript.json from transcribe")
    p_cut.add_argument("--out", required=True, help="output directory")
    p_cut.add_argument("--delete-words", default=None,
                       help='word indices, e.g. "12,13,20-25" (0-based)')
    p_cut.add_argument("--delete-text", default=None,
                       help='words to delete, e.g. "um, uh, you know"')
    p_cut.set_defaults(func=cmd_cut)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
