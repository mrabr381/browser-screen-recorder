"""Screen Recorder — local transcript editor (Streamlit).

Flow: upload a WebM recording (or load the bundled sample transcript) ->
transcribe locally with Whisper tiny -> tick words to delete -> cut the video
with ffmpeg -> download the edited video, SRT and transcript.

Nothing leaves this machine: transcription and cutting are 100% local.
"""

from __future__ import annotations

import os
import tempfile

import streamlit as st

from recorder.editor import export_all
from recorder.transcribe import check_ffmpeg, transcribe
from recorder.transcript import Transcript

st.set_page_config(page_title="Screen Recorder — Transcript Editor",
                   page_icon="●", layout="wide")
st.title("● Screen Recorder — Transcript Editor")
st.caption("Local only: record with the Chrome extension, transcribe with "
           "Whisper on your machine, delete words to cut the video. "
           "No server, no upload, no time limit.")

SAMPLE_TRANSCRIPT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "sample_data", "sample_transcript.json")


def _load_sample() -> Transcript | None:
    if os.path.exists(SAMPLE_TRANSCRIPT):
        return Transcript.from_json(SAMPLE_TRANSCRIPT)
    return None


# ---------------------------------------------------------------- session
if "transcript" not in st.session_state:
    st.session_state.transcript = None
if "video_path" not in st.session_state:
    st.session_state.video_path = None
if "video_name" not in st.session_state:
    st.session_state.video_name = None
if "deleted" not in st.session_state:
    st.session_state.deleted = set()

tab_record, tab_transcribe, tab_edit = st.tabs(
    ["1 · Record", "2 · Transcribe", "3 · Edit & export"])

# ------------------------------------------------------------------ record
with tab_record:
    st.subheader("Record with the Chrome extension")
    st.markdown("""
1. Open `chrome://extensions`, turn on **Developer mode**, click
   **Load unpacked** and pick this repo's `extension/` folder.
2. Click the extension icon → **Open recorder** → **Start recording**,
   then pick a screen, window or tab to share.
3. Stop when done — the WebM file lands in your Downloads folder.
4. Come back here (tab 2) and upload it, or use the sample transcript
   below to try the editor without recording anything.
""")
    if st.button("Load the bundled sample transcript"):
        sample = _load_sample()
        if sample is None:
            st.error("Sample transcript not found in sample_data/.")
        else:
            st.session_state.transcript = sample
            st.session_state.video_path = None
            st.session_state.video_name = "sample.webm (demo — no video file)"
            st.session_state.deleted = set()
            st.success(f"Loaded sample: {len(sample.words)} words, "
                       f"{sample.duration:.1f}s. Go to tab 3 to edit it.")

# -------------------------------------------------------------- transcribe
with tab_transcribe:
    st.subheader("Transcribe a recording")
    uploaded = st.file_uploader("Upload a WebM / MP4 recording",
                                type=["webm", "mp4", "mov", "mkv"])
    model = st.selectbox("Whisper model", ["tiny", "base", "small"],
                         help="tiny is fastest and needs ~75 MB on first run. "
                              "Larger models are more accurate but slower.")
    language = st.text_input("Language code (optional, blank = auto-detect)",
                             value="")
    if st.button("Transcribe", disabled=uploaded is None):
        try:
            check_ffmpeg()
        except RuntimeError as exc:
            st.error(str(exc))
        else:
            suffix = os.path.splitext(uploaded.name)[1]
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.write(uploaded.read())
            tmp.close()
            with st.spinner("Transcribing locally with Whisper "
                            "(first run downloads the model, ~75 MB)…"):
                try:
                    transcript = transcribe(
                        tmp.name, model_name=model,
                        language=language.strip() or None)
                except (RuntimeError, FileNotFoundError) as exc:
                    st.error(str(exc))
                else:
                    transcript.source = uploaded.name
                    st.session_state.transcript = transcript
                    st.session_state.video_path = tmp.name
                    st.session_state.video_name = uploaded.name
                    st.session_state.deleted = set()
                    st.success(f"Done — {len(transcript.words)} words, "
                               f"{transcript.duration:.1f}s, "
                               f"language {transcript.language or 'unknown'}.")

    transcript = st.session_state.transcript
    if transcript is not None:
        st.info(f"Loaded: **{st.session_state.video_name}** — "
                f"{len(transcript.words)} words, {transcript.duration:.1f}s.")

# --------------------------------------------------------------------- edit
with tab_edit:
    st.subheader("Edit the transcript — deleted words are cut from the video")
    transcript = st.session_state.transcript
    if transcript is None:
        st.warning("Nothing to edit yet — transcribe a recording or load "
                   "the sample transcript from tab 1.")
    else:
        deleted = st.session_state.deleted
        st.write(f"{len(transcript.words)} words · "
                 f"{len(deleted)} marked for deletion · "
                 f"{transcript.duration:.1f}s original")
        index_of = {id(w): i for i, w in enumerate(transcript.words)}
        for seg in transcript.segments(max_gap=1.2, include_deleted=True):
            # Chunk the segment's words into rows of 8 checkbox columns.
            for row_start in range(0, len(seg.words), 8):
                row = seg.words[row_start:row_start + 8]
                cols = st.columns(8)
                for col, word in zip(cols, row):
                    idx = index_of[id(word)]
                    with col:
                        checked = st.checkbox(
                            word.text, value=idx in deleted,
                            key=f"w{idx}")
                        if checked:
                            deleted.add(idx)
                        else:
                            deleted.discard(idx)
            st.caption(f"{seg.start:.1f}s – {seg.end:.1f}s")

        for i, w in enumerate(transcript.words):
            w.deleted = i in deleted

        kept = transcript.keep_ranges()
        edited_duration = sum(e - s for s, e in kept)
        st.write(f"After cuts: **{edited_duration:.1f}s** "
                 f"({transcript.duration - edited_duration:.1f}s removed)")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                "Download edited transcript",
                transcript.retime_after_cut().plain_text(),
                file_name="edited_transcript.txt", mime="text/plain")
        with col2:
            st.download_button(
                "Download subtitles (.srt)",
                transcript.retime_after_cut().to_srt(),
                file_name="edited.srt", mime="text/plain")
        with col3:
            if st.button("Cut the video (needs ffmpeg)",
                         disabled=st.session_state.video_path is None):
                try:
                    out_dir = tempfile.mkdtemp(prefix="recorder-edit-")
                    outputs = export_all(st.session_state.video_path,
                                         transcript, out_dir)
                    with open(outputs["edited_video"], "rb") as fh:
                        st.download_button(
                            "Download edited video (.webm)",
                            fh.read(), file_name="edited.webm",
                            mime="video/webm")
                    st.success(f"Cut done — edited video is "
                               f"{edited_duration:.1f}s.")
                except (RuntimeError, FileNotFoundError, ValueError) as exc:
                    st.error(str(exc))
        if st.session_state.video_path is None:
            st.caption("Video cutting needs the original recording file — "
                       "the sample transcript is text-only, so only the "
                       "transcript and SRT exports apply to it.")
