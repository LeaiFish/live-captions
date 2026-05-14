# Real-time Captions — Design Spec

**Date:** 2026-05-14  
**Goal:** A Mac app that shows live subtitles during in-person lectures to help the user stay focused.

---

## Overview

A lightweight Python app that captures microphone audio, transcribes it in real-time using Apple's built-in speech recognition, and displays a small floating subtitle window the user can drag to any corner of their screen.

---

## Architecture

Three modules, each with one responsibility:

```
main.py
├── recognizer.py   — Apple SFSpeechRecognizer via pyobjc
└── window.py       — Floating tkinter subtitle window
```

**Data flow:**  
Microphone → `recognizer.py` streams partial + final results → `main.py` passes text to `window.py` → window updates display.

---

## Components

### `recognizer.py` — Speech recognition

- Uses `pyobjc-framework-Speech` to access `SFSpeechRecognizer` and `AVAudioEngine`
- Language: `en-US`
- Streams recognition requests: emits partial results as the speaker talks, final result when a pause is detected
- Calls a provided callback `on_result(text: str, is_final: bool)` for each update
- Requests microphone permission on first run (macOS will show a system prompt)

### `window.py` — Subtitle window

- `tkinter` window, ~400×160px, no title bar, always on top (`wm_attributes("-topmost", True)`)
- Dark background (`#0f0f14`), rounded feel via padding
- Displays last 3 lines of transcript:
  - Oldest: `#3a3a4a` (dim gray)
  - Middle: `#6a6a7a` (medium gray)
  - Latest (current): `#ffffff` white, left accent bar in `#6c8eff` blue
  - Partial (in-progress): blue cursor `▋` below latest
- Draggable: click-and-drag anywhere on window moves it
- Close button: small `×` in top-right corner

### `main.py` — Entry point

- Initializes `recognizer` and `window`
- Receives `on_result` callbacks and appends final sentences to a history list (max 3)
- Passes history + current partial to window for display
- Runs `tkinter` main loop; recognition runs on a background thread

---

## Dependencies

```
pyobjc-framework-Speech
pyobjc-framework-AVFoundation
```

No audio capture library needed — `AVAudioEngine` is accessed via pyobjc directly alongside `SFSpeechRecognizer`.

---

## Setup

```bash
pip install pyobjc-framework-Speech pyobjc-framework-AVFoundation
python main.py
```

macOS will prompt for microphone access on first run. Must be run on macOS (Apple Silicon or Intel, 12.0+).

---

## Constraints & Out of Scope

- macOS only — no cross-platform support needed
- English only for now; language can be changed by swapping the locale string
- No settings UI, no persistence, no history saving
- No hotkey to pause/resume (can add later if needed)
