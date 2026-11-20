// Recording page: captures screen/tab/camera with getDisplayMedia +
// getUserMedia, records with MediaRecorder, saves a local WebM file.
//
// Nothing leaves this machine: no upload, no server, no analytics.
"use strict";

const $ = (id) => document.getElementById(id);
const preview = $("preview");
const statusEl = $("status");
const timerEl = $("timer");
const sizeEl = $("size");
const dotEl = $("dot");

let displayStream = null;
let cameraStream = null;
let micStream = null;
let outputStream = null;
let recorder = null;
let chunks = [];
let timerId = null;
let startedAt = 0;
let elapsedMs = 0;
let pausedAt = 0;
let lastBlob = null;
let canvasTimer = null;

function setStatus(text, isError = false) {
  statusEl.textContent = text;
  statusEl.classList.toggle("error", isError);
}

function fmtTime(ms) {
  const total = Math.floor(ms / 1000);
  const m = String(Math.floor(total / 60)).padStart(2, "0");
  const s = String(total % 60).padStart(2, "0");
  return `${m}:${s}`;
}

function tick() {
  elapsedMs = Date.now() - startedAt;
  timerEl.textContent = fmtTime(elapsedMs);
}

function pickMimeType() {
  const candidates = [
    "video/webm;codecs=vp9,opus",
    "video/webm;codecs=vp8,opus",
    "video/webm;codecs=vp9",
    "video/webm",
  ];
  for (const type of candidates) {
    if (window.MediaRecorder && MediaRecorder.isTypeSupported(type)) {
      return type;
    }
  }
  return "";
}

// Draw the screen video (and the camera in the corner) onto a canvas so a
// single stream can be recorded. Returns the canvas stream, or null when
// no camera is used (then the display stream is recorded directly).
function startCompositor(screenVideo, cameraVideo) {
  const canvas = document.createElement("canvas");
  const screenTrack = displayStream.getVideoTracks()[0];
  const settings = screenTrack.getSettings();
  canvas.width = settings.width || 1280;
  canvas.height = settings.height || 720;
  const ctx = canvas.getContext("2d");
  canvasTimer = setInterval(() => {
    ctx.drawImage(screenVideo, 0, 0, canvas.width, canvas.height);
    if (cameraVideo) {
      const w = Math.floor(canvas.width * 0.22);
      const h = Math.floor((w * cameraVideo.videoHeight) / Math.max(1, cameraVideo.videoWidth));
      ctx.drawImage(cameraVideo, canvas.width - w - 16, canvas.height - h - 16, w, h);
    }
  }, 1000 / 30);
  return canvas.captureStream(30);
}

async function startRecording() {
  try {
    displayStream = await navigator.mediaDevices.getDisplayMedia({
      video: true,
      audio: true,
    });
  } catch (err) {
    setStatus(`Screen share was not started (${err.name}). Click "Start recording" and pick a screen, window or tab.`, true);
    return;
  }

  const screenVideo = document.createElement("video");
  screenVideo.srcObject = displayStream;
  screenVideo.muted = true;
  await screenVideo.play().catch(() => {});

  let cameraVideo = null;
  if ($("camera").checked) {
    try {
      cameraStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      cameraVideo = document.createElement("video");
      cameraVideo.srcObject = cameraStream;
      cameraVideo.muted = true;
      await cameraVideo.play().catch(() => {});
    } catch (err) {
      setStatus(`Camera could not start (${err.name}) — recording the screen only.`, true);
    }
  }

  // Video: composited canvas when a camera is on, otherwise the raw display.
  let videoStream = displayStream;
  if (cameraVideo) {
    videoStream = startCompositor(screenVideo, cameraVideo);
  }

  // Audio: prefer the screen/tab audio; fall back to the microphone.
  const audioTracks = displayStream.getAudioTracks();
  let audioStream = null;
  if (audioTracks.length === 0 && $("mic").checked) {
    try {
      micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioStream = micStream;
    } catch (err) {
      setStatus(`Microphone unavailable (${err.name}) — recording without audio.`, true);
    }
  }

  outputStream = new MediaStream([
    ...videoStream.getVideoTracks(),
    ...(audioStream ? audioStream.getAudioTracks() : audioTracks),
  ]);
  preview.srcObject = outputStream;

  const mimeType = pickMimeType();
  chunks = [];
  try {
    recorder = new MediaRecorder(outputStream, mimeType ? { mimeType } : undefined);
  } catch (err) {
    setStatus(`This browser cannot record WebM (${err.message}).`, true);
    stopTracks();
    return;
  }
  recorder.ondataavailable = (event) => {
    if (event.data && event.data.size > 0) {
      chunks.push(event.data);
      sizeEl.textContent = `${(chunks.reduce((n, c) => n + c.size, 0) / 1048576).toFixed(1)} MB`;
    }
  };
  recorder.onstop = finishRecording;
  recorder.start(1000);

  // If the user stops sharing from the browser's own bar, stop cleanly too.
  displayStream.getVideoTracks()[0].addEventListener("ended", () => {
    if (recorder && recorder.state !== "inactive") recorder.stop();
  });

  startedAt = Date.now();
  timerId = setInterval(tick, 500);
  dotEl.classList.add("live");
  $("start").disabled = true;
  $("pause").disabled = false;
  $("stop").disabled = false;
  $("download").disabled = true;
  setStatus(`Recording${mimeType ? ` (${mimeType})` : ""} — share audio is ${audioTracks.length ? "on" : "off"}.`);
}

function finishRecording() {
  clearInterval(timerId);
  clearInterval(canvasTimer);
  dotEl.classList.remove("live");
  lastBlob = new Blob(chunks, { type: "video/webm" });
  $("download").disabled = false;
  $("start").disabled = false;
  $("pause").disabled = true;
  $("stop").disabled = true;
  $("pause").textContent = "Pause";
  setStatus(`Stopped — ${(lastBlob.size / 1048576).toFixed(1)} MB, ${fmtTime(elapsedMs)}. Click "Download recording" to save it.`);
  stopTracks();
  saveRecording();
}

function saveRecording() {
  if (!lastBlob) return;
  const stamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
  const filename = `screen-recording-${stamp}.webm`;
  const url = URL.createObjectURL(lastBlob);
  if (chrome && chrome.downloads) {
    chrome.downloads.download({ url, filename, saveAs: false }, () => {
      if (chrome.runtime.lastError) {
        setStatus(`Download failed (${chrome.runtime.lastError.message}) — use the Download button instead.`, true);
      } else {
        setStatus(`Saved to your Downloads folder as ${filename}.`);
      }
    });
  } else {
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
  }
}

function stopTracks() {
  for (const stream of [displayStream, cameraStream, micStream]) {
    if (stream) stream.getTracks().forEach((t) => t.stop());
  }
  displayStream = cameraStream = micStream = null;
}

$("start").addEventListener("click", startRecording);

$("pause").addEventListener("click", () => {
  if (!recorder) return;
  if (recorder.state === "recording") {
    recorder.pause();
    pausedAt = Date.now();
    $("pause").textContent = "Resume";
    setStatus("Paused.");
  } else if (recorder.state === "paused") {
    recorder.resume();
    startedAt += Date.now() - pausedAt;
    $("pause").textContent = "Pause";
    setStatus("Recording.");
  }
});

$("stop").addEventListener("click", () => {
  if (recorder && recorder.state !== "inactive") recorder.stop();
});

$("download").addEventListener("click", saveRecording);

$("open-app").addEventListener("click", () => {
  window.open("http://localhost:8501", "_blank");
});
