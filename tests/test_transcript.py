"""Tests for the Browser Screen Recorder transcript-cut maths.

Verified numbers from the bundled sample run (sample_data/):
33.608 s original, 82 words. Deleting words 27-35 ("These days a
chicken leg is a rare dish.") removes 10.88-13.12 s and leaves a
31.368 s video; cue 4 of the subtitles re-times from 14.37 s to 12.13 s.
Pure-Python module under test — no model, ffmpeg or Chrome needed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from recorder.transcript import (
    Transcript,
    format_timestamp,
    parse_timestamp,
)

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "sample_data" / "sample_transcript.json"


def load_sample() -> Transcript:
    return Transcript.from_json(str(SAMPLE))


def test_sample_transcript_loads():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert len(data["words"]) == 82
    assert data["duration"] == pytest.approx(33.608)
    transcript = load_sample()
    assert len(transcript.words) == 82
    assert transcript.duration == pytest.approx(33.608)


def test_delete_words_27_to_35():
    transcript = load_sample()
    deleted = transcript.delete_words(list(range(27, 36)))
    assert len(deleted) == 9
    assert [w.text for w in deleted] == [
        "These", "days", "a", "chicken", "leg", "is", "a", "rare", "dish.",
    ]
    assert len([w for w in transcript.words if not w.deleted]) == 73


def test_deleted_range_is_10_88_to_13_12():
    transcript = load_sample()
    transcript.delete_words(list(range(27, 36)))
    ranges = transcript.deleted_ranges()
    assert len(ranges) == 1
    assert ranges[0][0] == pytest.approx(10.88)
    assert ranges[0][1] == pytest.approx(13.12)


def test_keep_ranges():
    transcript = load_sample()
    transcript.delete_words(list(range(27, 36)))
    assert transcript.keep_ranges() == [
        pytest.approx((0.0, 10.88)),
        pytest.approx((13.12, 33.608)),
    ]


def test_edited_duration_is_31_368():
    # 33.608 - (13.12 - 10.88) = 31.368
    transcript = load_sample()
    transcript.delete_words(list(range(27, 36)))
    retimed = transcript.retime_after_cut()
    assert retimed.duration == pytest.approx(31.368)
    assert len(retimed.words) == 73
    # matches the shipped cuts.json
    cuts = json.loads(
        (ROOT / "sample_data" / "sample_output" / "cuts.json").read_text(
            encoding="utf-8"
        )
    )
    assert cuts["edited_duration"] == pytest.approx(31.368)
    assert cuts["removed_ranges"] == [[10.88, 13.12]]


def test_srt_retiming_cue_4():
    # Cue 4 ("Rice is often served in round bowls.") starts at 14.37 s
    # in the original; after cutting 2.24 s it must start at 12.13 s.
    transcript = load_sample()
    original = transcript.to_srt()
    assert "00:00:14,370" in original
    transcript.delete_words(list(range(27, 36)))
    retimed = transcript.retime_after_cut()
    rice = next(w for w in retimed.words if w.text == "Rice")
    assert rice.start == pytest.approx(12.13, abs=0.01)
    assert "00:00:12,130" in retimed.to_srt()
    # and the shipped edited.srt agrees
    edited_srt = (
        ROOT / "sample_data" / "sample_output" / "edited.srt"
    ).read_text(encoding="utf-8")
    assert "00:00:12,130" in edited_srt


def test_no_deletion_keeps_everything():
    transcript = load_sample()
    retimed = transcript.retime_after_cut()
    assert retimed.duration == pytest.approx(33.608)
    assert len(retimed.words) == 82


def test_timestamp_round_trip():
    for seconds in (0.0, 10.88, 12.13, 33.608, 3661.5):
        assert parse_timestamp(format_timestamp(seconds)) == pytest.approx(
            seconds, abs=0.001
        )
    assert format_timestamp(14.37) == "00:00:14,370"
    assert format_timestamp(12.13) == "00:00:12,130"


def test_srt_round_trip_preserves_words():
    transcript = load_sample()
    srt = transcript.to_srt()
    assert srt.count("-->") == 10  # 10 cues in the original sample
    reparsed = Transcript.from_srt(
        str(ROOT / "sample_data" / "sample_output" / "edited.srt")
    )
    assert len(reparsed.words) == 73
