// Browser Screen Recorder — live demo (demo/app.js)
//
// Static only: no server, no API keys, no upload.
// Part 1: in-browser recording via getDisplayMedia + MediaRecorder.
// Part 2: transcript editor using the REAL bundled sample transcript
// (sample_data/sample_transcript.json: 33.608 s, 82 words), with cut
// maths ported 1:1 from recorder/transcript.py so the demo reproduces
// the repo's verified numbers (delete words 27-35 -> 31.368 s).
//
// Honest status: the record/playback/download flow below is wired but
// has NOT been verified in a real browser in this sandbox (no display
// to capture, getDisplayMedia needs a real browser + user permission).
// The transcript cut maths ARE verified — see the node test in the
// handoff/report and tests/test_transcript.py.
"use strict";

/* ------------------------------------------------------------------ */
/* Sample transcript — copied verbatim from                        */
/* sample_data/sample_transcript.json (82 words, duration 33.608). */
/* ------------------------------------------------------------------ */
const SAMPLE_DURATION = 33.608;
const SAMPLE_WORDS = [{"text": "The", "start": 0.11, "end": 0.77, "deleted": false}, {"text": "birch", "start": 0.77, "end": 1.11, "deleted": false}, {"text": "can", "start": 1.11, "end": 1.39, "deleted": false}, {"text": "use", "start": 1.39, "end": 1.65, "deleted": false}, {"text": "lid", "start": 1.65, "end": 1.95, "deleted": false}, {"text": "on", "start": 1.95, "end": 2.25, "deleted": false}, {"text": "the", "start": 2.25, "end": 2.35, "deleted": false}, {"text": "smooth", "start": 2.35, "end": 2.69, "deleted": false}, {"text": "planks,", "start": 2.69, "end": 3.39, "deleted": false}, {"text": "glue", "start": 4.56, "end": 4.62, "deleted": false}, {"text": "the", "start": 4.62, "end": 4.9, "deleted": false}, {"text": "sheet", "start": 4.9, "end": 5.06, "deleted": false}, {"text": "to", "start": 5.06, "end": 5.3, "deleted": false}, {"text": "the", "start": 5.3, "end": 5.44, "deleted": false}, {"text": "dark", "start": 5.44, "end": 5.62, "deleted": false}, {"text": "blue", "start": 5.62, "end": 5.82, "deleted": false}, {"text": "background.", "start": 5.82, "end": 6.62, "deleted": false}, {"text": "It", "start": 8.03, "end": 8.07, "deleted": false}, {"text": "is", "start": 8.07, "end": 8.17, "deleted": false}, {"text": "easy", "start": 8.17, "end": 8.31, "deleted": false}, {"text": "to", "start": 8.31, "end": 8.59, "deleted": false}, {"text": "tell", "start": 8.59, "end": 8.71, "deleted": false}, {"text": "the", "start": 8.71, "end": 8.95, "deleted": false}, {"text": "depth", "start": 8.95, "end": 9.15, "deleted": false}, {"text": "of", "start": 9.15, "end": 9.41, "deleted": false}, {"text": "a", "start": 9.41, "end": 9.53, "deleted": false}, {"text": "well.", "start": 9.53, "end": 9.83, "deleted": false}, {"text": "These", "start": 10.93, "end": 11.17, "deleted": false}, {"text": "days", "start": 11.17, "end": 11.37, "deleted": false}, {"text": "a", "start": 11.37, "end": 11.65, "deleted": false}, {"text": "chicken", "start": 11.65, "end": 11.83, "deleted": false}, {"text": "leg", "start": 11.83, "end": 12.01, "deleted": false}, {"text": "is", "start": 12.01, "end": 12.23, "deleted": false}, {"text": "a", "start": 12.23, "end": 12.37, "deleted": false}, {"text": "rare", "start": 12.37, "end": 12.55, "deleted": false}, {"text": "dish.", "start": 12.55, "end": 13.07, "deleted": false}, {"text": "Rice", "start": 14.37, "end": 14.53, "deleted": false}, {"text": "is", "start": 14.53, "end": 14.81, "deleted": false}, {"text": "often", "start": 14.81, "end": 15.09, "deleted": false}, {"text": "served", "start": 15.09, "end": 15.37, "deleted": false}, {"text": "in", "start": 15.37, "end": 15.63, "deleted": false}, {"text": "round", "start": 15.63, "end": 15.87, "deleted": false}, {"text": "bowls.", "start": 15.87, "end": 16.25, "deleted": false}, {"text": "The", "start": 17.48, "end": 17.56, "deleted": false}, {"text": "juice", "start": 17.56, "end": 17.76, "deleted": false}, {"text": "of", "start": 17.76, "end": 18.0, "deleted": false}, {"text": "lemon", "start": 18.0, "end": 18.24, "deleted": false}, {"text": "makes", "start": 18.24, "end": 18.58, "deleted": false}, {"text": "fine", "start": 18.58, "end": 18.98, "deleted": false}, {"text": "punch.", "start": 18.98, "end": 19.42, "deleted": false}, {"text": "The", "start": 20.51, "end": 20.69, "deleted": false}, {"text": "box", "start": 20.69, "end": 20.93, "deleted": false}, {"text": "was", "start": 20.93, "end": 21.13, "deleted": false}, {"text": "thrown", "start": 21.13, "end": 21.37, "deleted": false}, {"text": "beside", "start": 21.37, "end": 21.71, "deleted": false}, {"text": "the", "start": 21.71, "end": 22.11, "deleted": false}, {"text": "pork", "start": 22.11, "end": 22.15, "deleted": false}, {"text": "truck.", "start": 22.15, "end": 22.55, "deleted": false}, {"text": "The", "start": 23.79, "end": 23.95, "deleted": false}, {"text": "hogs", "start": 23.95, "end": 24.29, "deleted": false}, {"text": "were", "start": 24.29, "end": 24.43, "deleted": false}, {"text": "fed", "start": 24.43, "end": 24.63, "deleted": false}, {"text": "chopped", "start": 24.63, "end": 24.99, "deleted": false}, {"text": "corn", "start": 24.99, "end": 25.27, "deleted": false}, {"text": "and", "start": 25.27, "end": 25.41, "deleted": false}, {"text": "garbage.", "start": 25.41, "end": 25.87, "deleted": false}, {"text": "Four", "start": 27.25, "end": 27.41, "deleted": false}, {"text": "hours", "start": 27.41, "end": 27.65, "deleted": false}, {"text": "a", "start": 27.65, "end": 27.89, "deleted": false}, {"text": "steady", "start": 27.89, "end": 28.03, "deleted": false}, {"text": "work", "start": 28.03, "end": 28.31, "deleted": false}, {"text": "faced", "start": 28.31, "end": 28.61, "deleted": false}, {"text": "us.", "start": 28.61, "end": 29.23, "deleted": false}, {"text": "A", "start": 30.22, "end": 30.3, "deleted": false}, {"text": "large", "start": 30.3, "end": 30.5, "deleted": false}, {"text": "size", "start": 30.5, "end": 30.78, "deleted": false}, {"text": "and", "start": 30.78, "end": 31.02, "deleted": false}, {"text": "stockings", "start": 31.02, "end": 31.36, "deleted": false}, {"text": "is", "start": 31.36, "end": 31.56, "deleted": false}, {"text": "hard", "start": 31.56, "end": 31.76, "deleted": false}, {"text": "to", "start": 31.76, "end": 32.04, "deleted": false}, {"text": "sell.", "start": 32.04, "end": 32.22, "deleted": false}];

/* ------------------------------------------------------------------ */
/* Cut maths — direct port of recorder/transcript.py.               */
/* ------------------------------------------------------------------ */

function formatTimestamp(seconds) {
  seconds = Math.max(0, Number(seconds));
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  let millis = Math.round((seconds - Math.floor(seconds)) * 1000);
  let s = secs;
  let m = minutes;
  let h = hours;
  if (millis === 1000) { s += 1; millis = 0; }
  if (s === 60) { m += 1; s = 0; }
  if (m === 60) { h += 1; m = 0; }
  const p2 = (n) => String(n).padStart(2, "0");
  const p3 = (n) => String(n).padStart(3, "0");
  return `${p2(h)}:${p2(m)}:${p2(s)},${p3(millis)}`;
}

function round3(n) { return Math.round(n * 1000) / 1000; }

// Consecutive deleted words, merged, padded by 0.05 s each side.
function deletedRanges(words, duration, pad) {
  pad = pad === undefined ? 0.05 : pad;
  const ranges = [];
  for (const w of words) {
    if (!w.deleted) continue;
    const start = Math.max(0, w.start - pad);
    const end = Math.min(duration, w.end + pad);
    if (ranges.length && start <= ranges[ranges.length - 1][1] + 0.05) {
      ranges[ranges.length - 1][1] = Math.max(ranges[ranges.length - 1][1], end);
    } else {
      ranges.push([start, end]);
    }
  }
  return ranges.map(([a, b]) => [round3(a), round3(b)]);
}

// Complement of deleted ranges; slivers < 0.05 s dropped, pieces
// separated by < 0.25 s merged.
function keepRanges(words, duration, pad, minGap) {
  pad = pad === undefined ? 0.05 : pad;
  minGap = minGap === undefined ? 0.25 : minGap;
  const removed = deletedRanges(words, duration, pad);
  const keep = [];
  let cursor = 0;
  for (const [start, end] of removed) {
    if (start > cursor) keep.push([cursor, start]);
    cursor = Math.max(cursor, end);
  }
  if (cursor < duration) keep.push([cursor, duration]);
  const merged = [];
  for (const [start, end] of keep) {
    if (end - start < 0.05) continue;
    if (merged.length && start - merged[merged.length - 1][1] < minGap) {
      merged[merged.length - 1][1] = end;
    } else {
      merged.push([start, end]);
    }
  }
  return merged.map(([a, b]) => [round3(a), round3(b)]);
}

// Kept words shifted to edited-video time; duration = sum of keep ranges.
function retimeAfterCut(words, duration) {
  const keep = keepRanges(words, duration);
  if (!keep.length) return { words: [], duration: 0 };
  function mapTime(t) {
    let offset = 0;
    for (const [start, end] of keep) {
      if (start <= t && t < end) return t - start + offset;
      offset += end - start;
    }
    return null;
  }
  const out = [];
  for (const w of words) {
    if (w.deleted) continue;
    const ns = mapTime(w.start);
    const ne = mapTime(w.end);
    if (ns === null || ne === null) continue;
    out.push({ text: w.text, start: round3(ns), end: round3(ne), deleted: false });
  }
  const newDuration = round3(keep.reduce((sum, [a, b]) => sum + (b - a), 0));
  return { words: out, duration: newDuration };
}

// Group kept words into segments, split on gaps > maxGap (default 0.8 s).
function segmentsOf(keptWords, maxGap) {
  maxGap = maxGap === undefined ? 0.8 : maxGap;
  const out = [];
  let current = [];
  for (const w of keptWords) {
    if (current.length && w.start - current[current.length - 1].end > maxGap) {
      out.push({ start: current[0].start, end: current[current.length - 1].end, words: current });
      current = [];
    }
    current.push(w);
  }
  if (current.length) {
    out.push({ start: current[0].start, end: current[current.length - 1].end, words: current });
  }
  return out;
}

function toSrt(retimedWords) {
  const lines = [];
  segmentsOf(retimedWords).forEach((seg, i) => {
    lines.push(String(i + 1));
    lines.push(`${formatTimestamp(seg.start)} --> ${formatTimestamp(seg.end)}`);
    lines.push(seg.words.map((w) => w.text).join(" "));
    lines.push("");
  });
  return lines.join("\n");
}

function plainText(words) {
  return words.filter((w) => !w.deleted).map((w) => w.text).join(" ");
}

function cutsReport(words, duration) {
  const retimed = retimeAfterCut(words, duration);
  return {
    source: "sample.webm",
    original_duration: duration,
    edited_duration: retimed.duration,
    words_total: words.length,
    words_deleted: words.filter((w) => w.deleted).length,
    removed_ranges: deletedRanges(words, duration),
    kept_ranges: keepRanges(words, duration),
  };
}

/* ------------------------------------------------------------------ */
/* Part 1: in-browser recorder (getDisplayMedia + MediaRecorder).   */
/* ------------------------------------------------------------------ */
const Recorder = {
  displayStream: null,
  micStream: null,
  recorder: null,
  chunks: [],
  blob: null,
  timerId: null,
  startedAt: 0,
  elapsedMs: 0,
  pausedAt: 0,
  mimeType: "",
};

function pickMimeType() {
  const candidates = [
    "video/webm;codecs=vp9,opus",
    "video/webm;codecs=vp8,opus",
    "video/webm;codecs=vp9",
    "video/webm",
  ];
  for (const type of candidates) {
    if (window.MediaRecorder && MediaRecorder.isTypeSupported(type)) return type;
  }
  return "";
}

function fmtClock(ms) {
  const total = Math.floor(ms / 1000);
  const m = String(Math.floor(total / 60)).padStart(2, "0");
  const s = String(total % 60).padStart(2, "0");
  return `${m}:${s}`;
}

function stopAllTracks() {
  for (const s of [Recorder.displayStream, Recorder.micStream]) {
    if (s) s.getTracks().forEach((t) => t.stop());
  }
  Recorder.displayStream = null;
  Recorder.micStream = null;
}

function updateRecMeta() {
  const size = Recorder.chunks.reduce((n, c) => n + c.size, 0);
  const sizeText = size ? `${(size / 1048576).toFixed(1)} MB` : "—";
  document.getElementById("rec-meta").textContent =
    `Time ${fmtClock(Recorder.elapsedMs)} · Size ${sizeText} · Format ${Recorder.mimeType || "—"}`;
}

function setRecStatus(text, isError) {
  const el = document.getElementById("rec-status");
  el.textContent = text;
  el.classList.toggle("error", !!isError);
}

async function startRecording() {
  const statusOk = window.navigator && navigator.mediaDevices && navigator.mediaDevices.getDisplayMedia;
  if (!statusOk) {
    setRecStatus("Screen capture is not available here: this browser (or origin) has no getDisplayMedia. Open this page in Chrome/Edge/Firefox over HTTPS or localhost.", true);
    return;
  }
  let displayStream;
  try {
    displayStream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
  } catch (err) {
    setRecStatus(`Screen share was not started (${err.name}). Click "Record" and pick a screen, window or tab.`, true);
    return;
  }
  Recorder.displayStream = displayStream;

  const preview = document.getElementById("preview");
  preview.srcObject = displayStream;
  preview.play().catch(() => {});

  // Mic fallback only when the shared screen carries no audio track.
  let micStream = null;
  const audioTracks = displayStream.getAudioTracks();
  if (audioTracks.length === 0 && document.getElementById("opt-mic").checked) {
    try {
      micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      Recorder.micStream = micStream;
    } catch (err) {
      setRecStatus(`Microphone unavailable (${err.name}) — recording without audio.`, true);
    }
  }

  const output = new MediaStream([
    ...displayStream.getVideoTracks(),
    ...(micStream ? micStream.getAudioTracks() : audioTracks),
  ]);

  Recorder.mimeType = pickMimeType();
  Recorder.chunks = [];
  Recorder.blob = null;
  try {
    Recorder.recorder = new MediaRecorder(output, Recorder.mimeType ? { mimeType: Recorder.mimeType } : undefined);
  } catch (err) {
    setRecStatus(`This browser cannot record WebM (${err.message}).`, true);
    stopAllTracks();
    return;
  }
  Recorder.recorder.ondataavailable = (event) => {
    if (event.data && event.data.size > 0) {
      Recorder.chunks.push(event.data);
      updateRecMeta();
    }
  };
  Recorder.recorder.onstop = finishRecording;
  Recorder.recorder.start(1000);

  // If the user stops sharing from the browser's own bar, stop cleanly too.
  const videoTrack = displayStream.getVideoTracks()[0];
  if (videoTrack) {
    videoTrack.addEventListener("ended", () => {
      if (Recorder.recorder && Recorder.recorder.state !== "inactive") Recorder.recorder.stop();
    });
  }

  Recorder.startedAt = Date.now();
  Recorder.elapsedMs = 0;
  Recorder.timerId = setInterval(() => {
    Recorder.elapsedMs = Date.now() - Recorder.startedAt;
    updateRecMeta();
  }, 500);
  document.getElementById("rec-dot").classList.add("live");
  document.getElementById("btn-record").disabled = true;
  document.getElementById("btn-pause").disabled = false;
  document.getElementById("btn-stop").disabled = false;
  document.getElementById("btn-download").disabled = true;
  setRecStatus(`Recording${Recorder.mimeType ? ` (${Recorder.mimeType})` : ""} — share audio is ${audioTracks.length ? "on" : "off"}.`);
  updateRecMeta();
}

function finishRecording() {
  clearInterval(Recorder.timerId);
  document.getElementById("rec-dot").classList.remove("live");
  Recorder.blob = new Blob(Recorder.chunks, { type: "video/webm" });
  const playback = document.getElementById("playback");
  playback.src = URL.createObjectURL(Recorder.blob);
  document.getElementById("btn-download").disabled = false;
  document.getElementById("btn-record").disabled = false;
  document.getElementById("btn-pause").disabled = true;
  document.getElementById("btn-stop").disabled = true;
  document.getElementById("btn-pause").textContent = "Pause";
  setRecStatus(`Stopped — ${(Recorder.blob.size / 1048576).toFixed(1)} MB, ${fmtClock(Recorder.elapsedMs)}. Play it back above or download it.`);
  updateRecMeta();
  stopAllTracks();
}

function downloadRecording() {
  if (!Recorder.blob) return;
  const stamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
  const a = document.createElement("a");
  a.href = URL.createObjectURL(Recorder.blob);
  a.download = `screen-recording-${stamp}.webm`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 60 * 1000);
}

/* ------------------------------------------------------------------ */
/* Part 2: transcript editor (live).                                */
/* ------------------------------------------------------------------ */
let editorWords = SAMPLE_WORDS.map((w) => ({ ...w }));

function downloadText(filename, text, mime) {
  const blob = new Blob([text], { type: mime || "text/plain;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 60 * 1000);
}

function renderEditor() {
  const wordsEl = document.getElementById("words");
  wordsEl.innerHTML = "";
  editorWords.forEach((w, i) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "word" + (w.deleted ? " deleted" : "");
    b.textContent = w.text;
    b.title = `#${i + 1} · ${w.start.toFixed(2)}–${w.end.toFixed(2)} s — click to ${w.deleted ? "restore" : "delete"}`;
    b.addEventListener("click", () => {
      editorWords[i].deleted = !editorWords[i].deleted;
      renderEditor();
    });
    wordsEl.appendChild(b);
  });

  const removed = deletedRanges(editorWords, SAMPLE_DURATION);
  const kept = keepRanges(editorWords, SAMPLE_DURATION);
  const retimed = retimeAfterCut(editorWords, SAMPLE_DURATION);
  const deletedCount = editorWords.filter((w) => w.deleted).length;
  const keptCount = editorWords.length - deletedCount;
  const srt = toSrt(retimed.words);
  const cueCount = segmentsOf(retimed.words).length;

  document.getElementById("stat-edited").textContent = `${retimed.duration.toFixed(3)} s`;
  document.getElementById("stat-saved").textContent =
    `${(SAMPLE_DURATION - retimed.duration).toFixed(3)} s saved`;
  document.getElementById("stat-kept").textContent =
    `${keptCount} kept · ${deletedCount} deleted`;
  document.getElementById("stat-cues").textContent = `${cueCount} cue${cueCount === 1 ? "" : "s"}`;
  document.getElementById("stat-ranges").textContent =
    `Removed ranges: ${removed.length ? JSON.stringify(removed) : "none"} · Kept ranges: ${JSON.stringify(kept)}`;

  const tl = document.getElementById("timeline");
  tl.innerHTML = "";
  // Interleave kept/cut spans across the full original duration.
  const spans = [];
  let cursor = 0;
  for (const [a, b] of removed) {
    if (a > cursor) spans.push(["kept", cursor, a]);
    spans.push(["cut", a, b]);
    cursor = Math.max(cursor, b);
  }
  if (cursor < SAMPLE_DURATION) spans.push(["kept", cursor, SAMPLE_DURATION]);
  if (!spans.length) spans.push(["kept", 0, SAMPLE_DURATION]);
  for (const [kind, a, b] of spans) {
    const d = document.createElement("div");
    d.className = kind;
    d.style.width = `${(((b - a) / SAMPLE_DURATION) * 100).toFixed(2)}%`;
    d.title = `${kind === "kept" ? "Kept" : "Cut"} ${a.toFixed(2)}–${b.toFixed(2)} s`;
    tl.appendChild(d);
  }

  const editedText = document.getElementById("edited-text");
  editedText.innerHTML = "";
  editorWords.forEach((w, i) => {
    if (i) editedText.appendChild(document.createTextNode(" "));
    if (w.deleted) {
      const s = document.createElement("s");
      s.textContent = w.text;
      editedText.appendChild(s);
    } else {
      editedText.appendChild(document.createTextNode(w.text));
    }
  });

  document.getElementById("srt-output").textContent = srt || "(everything deleted — no cues left)";

  document.getElementById("btn-dl-srt").onclick = () => downloadText("edited.srt", srt, "text/plain;charset=utf-8");
  document.getElementById("btn-dl-txt").onclick = () => downloadText("edited_transcript.txt", plainText(editorWords) + "\n", "text/plain;charset=utf-8");
  document.getElementById("btn-dl-cuts").onclick = () =>
    downloadText("cuts.json", JSON.stringify(cutsReport(editorWords, SAMPLE_DURATION), null, 2) + "\n", "application/json");
}

/* ------------------------------------------------------------------ */
/* Wire-up (browser only).                                          */
/* ------------------------------------------------------------------ */
if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("btn-record").addEventListener("click", startRecording);
    document.getElementById("btn-pause").addEventListener("click", () => {
      const r = Recorder.recorder;
      if (!r) return;
      if (r.state === "recording") {
        r.pause();
        Recorder.pausedAt = Date.now();
        document.getElementById("btn-pause").textContent = "Resume";
        setRecStatus("Paused.");
      } else if (r.state === "paused") {
        r.resume();
        Recorder.startedAt += Date.now() - Recorder.pausedAt;
        document.getElementById("btn-pause").textContent = "Pause";
        setRecStatus("Recording.");
      }
    });
    document.getElementById("btn-stop").addEventListener("click", () => {
      if (Recorder.recorder && Recorder.recorder.state !== "inactive") Recorder.recorder.stop();
    });
    document.getElementById("btn-download").addEventListener("click", downloadRecording);
    document.getElementById("btn-delete-sample").addEventListener("click", () => {
      for (let i = 27; i <= 35; i++) editorWords[i].deleted = true;
      renderEditor();
    });
    document.getElementById("btn-reset-words").addEventListener("click", () => {
      editorWords = SAMPLE_WORDS.map((w) => ({ ...w }));
      renderEditor();
    });
    renderEditor();
  });
}

// Node export — lets the cut maths be tested headlessly (node --check
// + require). Harmless in the browser.
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    SAMPLE_DURATION,
    SAMPLE_WORDS,
    formatTimestamp,
    deletedRanges,
    keepRanges,
    retimeAfterCut,
    segmentsOf,
    toSrt,
    plainText,
    cutsReport,
  };
}
