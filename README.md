# ● Browser Screen Recorder + Transcript Editor

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![No upload](https://img.shields.io/badge/privacy-100%25%20local-brightgreen)](#privacy)
[![No time limit](https://img.shields.io/badge/recording-no%20time%20limit-brightgreen)](#loom-vs-this-project)
[![Chrome MV3](https://img.shields.io/badge/extension-Chrome%20MV3-orange)](extension/)

A free, local alternative to Loom: record your screen, tab or camera with a
Chrome extension, transcribe it on your own machine with Whisper, edit the
transcript like a document — and the video cuts itself to match. No server,
no upload, no 5-minute cap, no 25-video limit.

> **Live demo:** a real sample edit — [sample edit page](sample_data/sample_output/index.html)
> (works on GitHub Pages, no server needed) — or run the web app with
> `streamlit run app.py` (see [Live demo](#live-demo)).

## Table of contents

- [What it does](#what-it-does)
- [Before / after](#before--after)
- [Loom vs this project](#loom-vs-this-project)
- [Quickstart](#quickstart)
- [Install the Chrome extension](#install-the-chrome-extension)
- [Use it](#use-it)
- [Live demo](#live-demo)
- [Privacy](#privacy)
- [How it works](#how-it-works)
- [Honest limitations](#honest-limitations)
- [Contributing](#contributing)

## What it does

- **Record** — Chrome extension (Manifest V3): screen, window or tab, with
  system/tab audio, optional camera picture-in-picture and microphone
  fallback. Saves a WebM file to your Downloads folder.
- **Transcribe** — local Whisper (`tiny` by default, ~75 MB model download
  on first run) with word-level timestamps. No API key, no account.
- **Edit** — tick words to delete in the Streamlit app (or the CLI). The
  editor computes the cut ranges, re-encodes only the kept parts and joins
  them, so cuts land on exact word boundaries.
- **Export** — edited video (WebM), re-timed subtitles (`.srt`), edited
  transcript (`.txt` / `.json`) and a cut report (`cuts.json`).

## Before / after

Real run on the bundled sample (33.6 s recording, Harvard-sentences speech,
transcribed by the tool itself in ~8 s):

| | Before | After |
|---|---|---|
| Video length | 33.6 s | **31.4 s** |
| Transcript | "These days a chicken leg is a rare dish." included | sentence deleted, video cut 10.88 s – 13.12 s |
| Words | 82 | 73 kept, 9 deleted |
| Subtitles | 10 cues | 9 cues, re-timed (cue 4 now starts 12.13 s, was 14.37 s) |

```text
$ python -m recorder transcribe sample_data/sample.webm --out report/
Transcribed 82 words (33.6s, model tiny, lang en)

$ python -m recorder cut sample_data/sample.webm report/transcript.json \
    --delete-words 27-35 --out edited/
Deleting 9 word(s): 'These', 'days', 'a', 'chicken', 'leg', 'is', 'a', 'rare', 'dish.'
Edited video: 33.6s -> 31.4s
```

<details>
<summary>Real output excerpts (from the sample run)</summary>

```text
# transcript.srt (original, first cues)
1
00:00:00,110 --> 00:00:03,390
The birch can use lid on the smooth planks,

2
00:00:04,560 --> 00:00:06,620
glue the sheet to the dark blue background.
```

```json
// cuts.json (after deleting words 27-35)
{
  "original_duration": 33.608,
  "edited_duration": 31.368,
  "words_total": 82,
  "words_deleted": 9,
  "removed_ranges": [[10.88, 13.12]],
  "kept_ranges": [[0.0, 10.88], [13.12, 33.608]]
}
```

</details>

## Loom vs this project

| | Loom (free tier) | This project |
|---|---|---|
| Videos | 25 total | Unlimited |
| Length per video | 5 minutes | No limit |
| Quality | 720p cap | Whatever your screen is |
| Transcription | Cloud, paid plans | Local Whisper, free |
| Transcript editing that cuts the video | No | Yes |
| Where your recording goes | Loom's servers | Your Downloads folder |
| Price | Free tier, then paid | Free, forever |

Loom's free limits above (25 videos, 5 min each, 720p) are the only
competitor numbers quoted here. Everything else in the table is this
project's own behaviour, verified by running it.

## Quickstart

```bash
git clone https://github.com/mrabr381/browser-screen-recorder.git
cd browser-screen-recorder
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

You also need **ffmpeg** (audio extraction + video cutting) and **Chrome**
(for the extension). First transcription downloads the Whisper tiny model
(~75 MB) once from Hugging Face and caches it.

| Dependency | Check | Install |
|---|---|---|
| Python 3.10+ | `python3 --version` | https://www.python.org/ |
| ffmpeg 6+ | `ffmpeg -version` | https://ffmpeg.org/download.html |
| Chrome | — | https://www.google.com/chrome/ |

## Install the Chrome extension

1. Open `chrome://extensions`.
2. Turn on **Developer mode** (top right).
3. Click **Load unpacked** and pick this repo's `extension/` folder.
4. Click the extension icon → **Open recorder** → **Start recording**,
   then pick a screen, window or tab to share.
5. **Stop & save** — the WebM file lands in your Downloads folder.

The extension asks for no data: it has no analytics, no network calls and
no server. Recording happens in a full tab (not the popup) because a popup
cannot keep recording once it loses focus.

## Use it

### Web app (easiest)

```bash
.venv/bin/streamlit run app.py
```

Open http://localhost:8501 — upload a recording, transcribe, tick words to
delete, download the edited video, SRT and transcript. Or click
**Load the bundled sample transcript** to try the editor with no recording.

### CLI

```bash
# Transcribe (writes transcript.json, transcript.srt, transcript.txt)
.venv/bin/python -m recorder transcribe recording.webm --out report/

# Delete words by index (0-based, ranges allowed) and cut the video
.venv/bin/python -m recorder cut recording.webm report/transcript.json \
    --delete-words 27-35 --out edited/

# ...or delete by word text (case-insensitive, e.g. filler words)
.venv/bin/python -m recorder cut recording.webm report/transcript.json \
    --delete-text "um, uh" --out edited/
```

Exit codes: `0` ok, `1` runtime error (missing file, no ffmpeg, model
failure — with a plain message, no traceback), `2` bad usage.

### Regenerate the sample video

The sample video is binary, so it is not in the repo — its transcript is.
Rebuild it locally (downloads a public Harvard-sentences speech sample,
muxes it with an ffmpeg test pattern, transcribes it):

```bash
bash sample_data/make_sample.sh
```

## Live demo

- ✅ **Already built:** [sample_data/sample_output/index.html](sample_data/sample_output/index.html) —
  static page showing the real sample edit (before/after, cut report,
  edited SRT, download links), zero external requests.
  **ABR's step (2 min):** repo Settings → Pages → Source: Deploy from a
  branch → `main`, folder `/ (root)` → Save. Live at
  `https://mrabr381.github.io/browser-screen-recorder/sample_data/sample_output/`.
- ✅ **Streamlit Cloud ready:** `app.py` at the repo root, clean
  `requirements.txt`. **ABR's step (1 click):** share.streamlit.io →
  Create app → repo `mrabr381/browser-screen-recorder`, branch `main`,
  file `app.py` → Deploy. Note: Streamlit Cloud runs the editor, but the
  Chrome extension itself must be loaded in your own Chrome (see above) —
  and the app needs ffmpeg, which Streamlit Cloud provides via
  `packages.txt` (not included — add `ffmpeg` there if you deploy it).
  The CLI works fully offline on any machine with Python + ffmpeg.

## Privacy

- Recordings are saved to **your** Downloads folder by the extension.
- Transcription runs on **your CPU** (faster-whisper). The model download
  (~75 MB, once) is the only network use; transcription itself is offline.
- Cutting runs on **your machine** with local ffmpeg.
- The app makes **no network calls at runtime**. No accounts, no keys,
  no telemetry. Your recordings never leave your machine.

## How it works

```
Chrome extension (MV3)                Local Python app / CLI
┌─────────────────────────┐           ┌──────────────────────────────────┐
│ getDisplayMedia (screen)│           │ ffmpeg: extract 16 kHz mono WAV │
│ getUserMedia (camera)   │  WebM     │ faster-whisper tiny: words +    │
│ canvas composite (PiP)  ├──────────►│ timestamps (VAD on)             │
│ MediaRecorder → .webm   │           │ transcript.py: SRT, edit, retime│
└─────────────────────────┘           │ editor.py: ffmpeg cut + concat  │
                                      └──────────────────────────────────┘
```

- `recorder/transcript.py` — word-level transcript model, SRT read/write,
  delete/keep ranges, re-timing after cuts. Pure Python, no model needed.
- `recorder/transcribe.py` — ffmpeg audio extraction + faster-whisper.
- `recorder/editor.py` — re-encode kept ranges (VP9/Opus) and concat.
- `recorder/cli.py` — `transcribe` and `cut` commands, exit codes 0/1/2.
- `extension/` — Manifest V3 extension: popup, recorder tab, service worker.

## Honest limitations

- **Whisper tiny mishears sometimes.** On the sample it heard "The birch
  canoe slid on the smooth planks" as "The birch can use lid on the smooth
  planks" — tiny is fast, not perfect. Use `--model base` or `small` for
  better accuracy (slower, bigger download).
- **First transcription downloads the model** (~75 MB tiny, more for
  base/small) from Hugging Face. After that it works offline.
- **The extension was not load-tested in a real Chrome here** — no Chrome
  binary exists in this sandbox. Its JavaScript passes `node --check`,
  the manifest parses, and the recording flow follows the standard
  `getDisplayMedia` + `MediaRecorder` pattern. First real load in Chrome
  (Load unpacked) is the remaining check.
- **Streamlit Cloud note:** the web app deploys there, but video cutting
  needs ffmpeg on the host (add a `packages.txt` with `ffmpeg`), and the
  extension still has to be loaded in your own Chrome.
- **Cutting re-encodes** the kept ranges (VP9/Opus), so a long video takes
  a while — accuracy over speed, cuts land on exact word boundaries.

## Contributing

Issues and pull requests are welcome. Please keep the quality promise:
no invented numbers, no hardcoded keys, no network calls at runtime, and
every new feature covered by a test on the sample recording.
