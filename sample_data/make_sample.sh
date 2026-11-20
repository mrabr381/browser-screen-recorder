#!/usr/bin/env bash
# Regenerate sample_data/sample.webm locally (the file itself is binary, so
# it is gitignored — the repo ships the transcript, not the video).
#
# The audio is the public Harvard-sentences test recording from
# voiptroubleshooter.com (33.6 s, male voice, 8 kHz WAV). The video track is
# an ffmpeg-generated test pattern. No real person was recorded for this demo.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -f sample.webm ]; then
  echo "Downloading public-domain speech sample (Harvard sentences)..."
  curl -sL --max-time 120 -o /tmp/sample_speech.wav \
    "https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0010_8k.wav"
  echo "Muxing test video + speech into sample.webm..."
  ffmpeg -y -v error \
    -f lavfi -i "testsrc=duration=33.6:size=1280x720:rate=30" \
    -i /tmp/sample_speech.wav \
    -map 0:v -map 1:a -c:v libvpx-vp9 -b:v 0 -crf 32 \
    -c:a libopus -b:a 96k -shortest sample.webm
  rm -f /tmp/sample_speech.wav
fi

echo "Transcribing sample.webm with local Whisper (first run downloads the tiny model, ~75 MB)..."
cd ..
if [ -x .venv/bin/python ]; then
  PY=.venv/bin/python
else
  PY=python3
fi
TMP_OUT="$(mktemp -d)"
"$PY" -m recorder transcribe sample_data/sample.webm --out "$TMP_OUT"
cp "$TMP_OUT/transcript.json" sample_data/sample_transcript.json
rm -rf "$TMP_OUT"
echo "Done: sample_data/sample.webm + sample_data/sample_transcript.json"
