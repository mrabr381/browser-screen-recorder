"""Transcript data model: words with timestamps, SRT import/export, edits.

Everything here is pure Python (no network, no Whisper) so the editor can
be tested on bundled sample data without a model download.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field


def format_timestamp(seconds: float) -> str:
    """Seconds -> SRT timestamp HH:MM:SS,mmm (clamped at 0, rounded to ms)."""
    seconds = max(0.0, float(seconds))
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis == 1000:  # rounding carried over a second boundary
        secs += 1
        millis = 0
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def parse_timestamp(text: str) -> float:
    """SRT timestamp HH:MM:SS,mmm -> seconds."""
    match = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)", text.strip())
    if not match:
        raise ValueError(f"not an SRT timestamp: {text!r}")
    hours, minutes, secs, millis = (int(g) for g in match.groups())
    return hours * 3600 + minutes * 60 + secs + millis / 1000.0


@dataclass
class Word:
    text: str
    start: float
    end: float
    deleted: bool = False

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass
class Segment:
    start: float
    end: float
    words: list[Word] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(w.text for w in self.words if not w.deleted)


@dataclass
class Transcript:
    words: list[Word] = field(default_factory=list)
    source: str = ""
    model: str = ""
    language: str = ""
    duration: float = 0.0

    # -- construction -----------------------------------------------------
    @classmethod
    def from_whisper(cls, segments, source: str = "", model: str = "",
                     language: str = "") -> "Transcript":
        words: list[Word] = []
        duration = 0.0
        for seg in segments:
            for w in getattr(seg, "words", None) or []:
                words.append(Word(text=w.word.strip(),
                                  start=float(w.start), end=float(w.end)))
                duration = max(duration, float(w.end))
            duration = max(duration, float(seg.end))
        words.sort(key=lambda w: w.start)
        return cls(words=words, source=source, model=model,
                   language=language, duration=duration)

    @classmethod
    def from_json(cls, path: str) -> "Transcript":
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        words = [Word(text=w["text"], start=float(w["start"]),
                      end=float(w["end"]), deleted=bool(w.get("deleted", False)))
                 for w in data["words"]]
        return cls(words=words, source=data.get("source", ""),
                   model=data.get("model", ""), language=data.get("language", ""),
                   duration=float(data.get("duration", 0.0)))

    def to_json(self, path: str) -> None:
        data = {
            "source": self.source,
            "model": self.model,
            "language": self.language,
            "duration": self.duration,
            "words": [{"text": w.text, "start": round(w.start, 3),
                       "end": round(w.end, 3), "deleted": w.deleted}
                      for w in self.words],
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)

    # -- segments ---------------------------------------------------------
    def segments(self, max_gap: float = 0.8,
                 include_deleted: bool = False) -> list[Segment]:
        """Group words into display segments, split on gaps > max_gap.

        By default only kept words are returned (for SRT/export); pass
        include_deleted=True for the editor, so a deleted word stays
        visible and can be un-ticked.
        """
        kept = self.words if include_deleted else \
            [w for w in self.words if not w.deleted]
        out: list[Segment] = []
        current: list[Word] = []
        for word in kept:
            if current and word.start - current[-1].end > max_gap:
                out.append(Segment(start=current[0].start, end=current[-1].end,
                                   words=current))
                current = []
            current.append(word)
        if current:
            out.append(Segment(start=current[0].start, end=current[-1].end,
                               words=current))
        return out

    def plain_text(self) -> str:
        return " ".join(w.text for w in self.words if not w.deleted)

    # -- SRT --------------------------------------------------------------
    def to_srt(self) -> str:
        """One cue per segment; cue text is the kept words of that segment."""
        lines: list[str] = []
        for i, seg in enumerate(self.segments(), start=1):
            lines.append(str(i))
            lines.append(f"{format_timestamp(seg.start)} --> "
                         f"{format_timestamp(seg.end)}")
            lines.append(seg.text)
            lines.append("")
        return "\n".join(lines)

    @classmethod
    def from_srt(cls, path: str, source: str = "") -> "Transcript":
        with open(path, encoding="utf-8") as fh:
            raw = fh.read()
        blocks = [b.strip() for b in re.split(r"\n\s*\n", raw.strip()) if b.strip()]
        words: list[Word] = []
        duration = 0.0
        for block in blocks:
            block_lines = block.splitlines()
            if len(block_lines) < 3:
                continue
            timing = block_lines[1] if block_lines[0].strip().isdigit() else block_lines[0]
            start_s, _, end_s = timing.partition(" --> ")
            start, end = parse_timestamp(start_s), parse_timestamp(end_s)
            text = " ".join(block_lines[2:] if block_lines[0].strip().isdigit()
                            else block_lines[1:])
            tokens = text.split()
            if not tokens:
                continue
            span = max(0.01, end - start)
            step = span / len(tokens)
            for j, token in enumerate(tokens):
                words.append(Word(text=token, start=start + j * step,
                                  end=start + (j + 1) * step))
            duration = max(duration, end)
        words.sort(key=lambda w: w.start)
        return cls(words=words, source=source, duration=duration)

    # -- editing ----------------------------------------------------------
    def delete_words(self, indices: list[int]) -> list[Word]:
        """Mark words deleted by 0-based index; returns the deleted words."""
        removed: list[Word] = []
        for i in indices:
            if 0 <= i < len(self.words) and not self.words[i].deleted:
                self.words[i].deleted = True
                removed.append(self.words[i])
        return removed

    def deleted_ranges(self, pad: float = 0.05) -> list[tuple[float, float]]:
        """Time ranges to cut out: consecutive deleted words, merged, padded."""
        ranges: list[tuple[float, float]] = []
        for w in self.words:
            if not w.deleted:
                continue
            start = max(0.0, w.start - pad)
            end = min(self.duration, w.end + pad)
            if ranges and start <= ranges[-1][1] + 0.05:
                ranges[-1] = (ranges[-1][0], max(ranges[-1][1], end))
            else:
                ranges.append((start, end))
        return ranges

    def keep_ranges(self, pad: float = 0.05,
                    min_gap: float = 0.25) -> list[tuple[float, float]]:
        """Time ranges to keep: complement of deleted ranges, tiny pieces merged."""
        removed = self.deleted_ranges(pad=pad)
        keep: list[tuple[float, float]] = []
        cursor = 0.0
        for start, end in removed:
            if start > cursor:
                keep.append((cursor, start))
            cursor = max(cursor, end)
        if cursor < self.duration:
            keep.append((cursor, self.duration))
        merged: list[tuple[float, float]] = []
        for start, end in keep:
            if end - start < 0.05:
                continue  # sliver too short to cut cleanly; drop it
            if merged and start - merged[-1][1] < min_gap:
                merged[-1] = (merged[-1][0], end)
            else:
                merged.append((start, end))
        return merged

    def retime_after_cut(self) -> "Transcript":
        """New transcript with kept words shifted to edited-video time."""
        keep = self.keep_ranges()
        if not keep:
            return Transcript(words=[], source=self.source, model=self.model,
                              language=self.language, duration=0.0)

        def map_time(t: float) -> float | None:
            offset = 0.0
            for start, end in keep:
                if start <= t < end:
                    return t - start + offset
                offset += end - start
            return None

        new_words: list[Word] = []
        for w in self.words:
            if w.deleted:
                continue
            new_start = map_time(w.start)
            new_end = map_time(w.end)
            if new_start is None or new_end is None:
                continue
            new_words.append(Word(text=w.text, start=new_start, end=new_end))
        new_duration = sum(end - start for start, end in keep)
        return Transcript(words=new_words, source=self.source, model=self.model,
                          language=self.language, duration=new_duration)
