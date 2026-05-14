# Real-time Captions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A macOS Python app that captures microphone audio and displays live rolling subtitles in a small always-on-top draggable window.

**Architecture:** Three modules — `recognizer.py` wraps Apple's `SFSpeechRecognizer` via pyobjc and streams partial/final results via callback; `window.py` owns the tkinter floating window and maintains a 3-line rolling history; `main.py` wires them together and runs the event loop.

**Tech Stack:** Python 3.11+, pyobjc-framework-Speech, pyobjc-framework-AVFoundation, tkinter (stdlib)

---

## File Map

| File | Role |
|------|------|
| `requirements.txt` | Pinned dependencies |
| `history.py` | Pure history-buffer logic (testable, no UI) |
| `window.py` | tkinter floating subtitle window |
| `recognizer.py` | Apple SFSpeechRecognizer wrapper |
| `main.py` | Entry point — wires recognizer → history → window |
| `tests/test_history.py` | Unit tests for history buffer |
| `tests/test_window.py` | Smoke test: window opens and renders text |

---

## Task 1: Project setup

**Files:**
- Create: `requirements.txt`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
pyobjc-framework-Speech==10.3.1
pyobjc-framework-AVFoundation==10.3.1
```

- [ ] **Step 2: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: both packages install without error. If version not found, replace with latest: `pip install pyobjc-framework-Speech pyobjc-framework-AVFoundation` then pin to what installed.

- [ ] **Step 3: Create empty test package**

```bash
mkdir -p tests && touch tests/__init__.py
```

- [ ] **Step 4: Verify Python and tkinter are available**

```bash
python -c "import tkinter; print('tkinter ok')"
```

Expected: `tkinter ok`

- [ ] **Step 5: Commit**

```bash
git add requirements.txt tests/__init__.py
git commit -m "chore: project setup"
```

---

## Task 2: History buffer

The history buffer holds the last N final sentences plus one in-progress partial. Keeping it pure (no UI, no threads) makes it easy to test.

**Files:**
- Create: `history.py`
- Create: `tests/test_history.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_history.py`:
```python
from history import History

def test_starts_empty():
    h = History(max_lines=3)
    assert h.lines == []
    assert h.partial == ""

def test_partial_update():
    h = History(max_lines=3)
    h.update("hello world", is_final=False)
    assert h.partial == "hello world"
    assert h.lines == []

def test_final_appends_to_lines():
    h = History(max_lines=3)
    h.update("first sentence.", is_final=True)
    assert h.lines == ["first sentence."]
    assert h.partial == ""

def test_max_lines_evicts_oldest():
    h = History(max_lines=3)
    for i in range(4):
        h.update(f"sentence {i}.", is_final=True)
    assert len(h.lines) == 3
    assert h.lines[0] == "sentence 1."
    assert h.lines[-1] == "sentence 3."

def test_display_returns_correct_structure():
    h = History(max_lines=3)
    h.update("one.", is_final=True)
    h.update("two.", is_final=True)
    h.update("in progress", is_final=False)
    d = h.display()
    assert d["lines"] == ["one.", "two."]
    assert d["partial"] == "in progress"
```

- [ ] **Step 2: Run to confirm all fail**

```bash
python -m pytest tests/test_history.py -v
```

Expected: 5 failures (ImportError or similar)

- [ ] **Step 3: Implement history.py**

```python
class History:
    def __init__(self, max_lines: int = 3):
        self.max_lines = max_lines
        self.lines: list[str] = []
        self.partial: str = ""

    def update(self, text: str, is_final: bool) -> None:
        if is_final:
            self.lines.append(text)
            if len(self.lines) > self.max_lines:
                self.lines.pop(0)
            self.partial = ""
        else:
            self.partial = text

    def display(self) -> dict:
        return {"lines": list(self.lines), "partial": self.partial}
```

- [ ] **Step 4: Run tests — all should pass**

```bash
python -m pytest tests/test_history.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add history.py tests/test_history.py
git commit -m "feat: history buffer with tests"
```

---

## Task 3: Subtitle window

**Files:**
- Create: `window.py`
- Create: `tests/test_window.py`

- [ ] **Step 1: Write a smoke test for the window**

`tests/test_window.py`:
```python
import tkinter as tk
import pytest
from window import SubtitleWindow

@pytest.fixture
def root():
    r = tk.Tk()
    yield r
    r.destroy()

def test_window_creates_without_error(root):
    w = SubtitleWindow(root)
    assert w is not None

def test_render_updates_without_error(root):
    w = SubtitleWindow(root)
    w.render(lines=["first.", "second."], partial="in prog")
    root.update_idletasks()
```

- [ ] **Step 2: Run to confirm tests fail**

```bash
python -m pytest tests/test_window.py -v
```

Expected: ImportError (window.py doesn't exist)

- [ ] **Step 3: Implement window.py**

```python
import tkinter as tk

COLORS = {
    "bg": "#0f0f14",
    "old": "#3a3a4a",
    "mid": "#6a6a7a",
    "current": "#ffffff",
    "accent": "#6c8eff",
    "cursor": "#6c8eff",
}
FONT = ("System", 13)
FONT_SMALL = ("System", 12)


class SubtitleWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Live Captions")
        root.geometry("460x170+100+900")
        root.configure(bg=COLORS["bg"])
        root.wm_attributes("-topmost", True)
        root.overrideredirect(True)  # remove title bar

        self._drag_x = 0
        self._drag_y = 0
        root.bind("<ButtonPress-1>", self._drag_start)
        root.bind("<B1-Motion>", self._drag_move)

        # Close button
        close = tk.Label(root, text="×", bg=COLORS["bg"],
                         fg=COLORS["mid"], font=("System", 16), cursor="hand2")
        close.place(relx=1.0, x=-12, y=4, anchor="ne")
        close.bind("<Button-1>", lambda _: root.destroy())

        # Label area
        self._frame = tk.Frame(root, bg=COLORS["bg"])
        self._frame.pack(fill="both", expand=True, padx=14, pady=(24, 10))

        self._labels: list[tk.Label] = []
        self._accent: list[tk.Frame] = []
        for _ in range(3):  # old, mid, current
            row = tk.Frame(self._frame, bg=COLORS["bg"])
            row.pack(fill="x", pady=2)
            bar = tk.Frame(row, width=3, bg=COLORS["bg"])
            bar.pack(side="left", fill="y", padx=(0, 6))
            lbl = tk.Label(row, text="", bg=COLORS["bg"], fg=COLORS["old"],
                           font=FONT_SMALL, anchor="w", wraplength=400,
                           justify="left")
            lbl.pack(side="left", fill="x", expand=True)
            self._labels.append(lbl)
            self._accent.append(bar)

        self._cursor_label = tk.Label(self._frame, text="", bg=COLORS["bg"],
                                      fg=COLORS["cursor"], font=FONT, anchor="w")
        self._cursor_label.pack(fill="x", padx=(9, 0))

    def render(self, lines: list[str], partial: str) -> None:
        color_map = [COLORS["old"], COLORS["mid"], COLORS["current"]]
        # Pad lines to always fill 3 slots
        padded = ([""] * (3 - len(lines)) + lines)[-3:]
        for i, (lbl, bar, text) in enumerate(zip(self._labels, self._accent, padded)):
            lbl.configure(text=text, fg=color_map[i])
            is_current = (i == 2 and text)
            bar.configure(bg=COLORS["accent"] if is_current else COLORS["bg"])
        self._cursor_label.configure(text="▋" if partial else "")
        if partial:
            self._labels[2].configure(text=partial, fg=COLORS["current"])
            self._accent[2].configure(bg=COLORS["accent"])

    def _drag_start(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _drag_move(self, event):
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")
```

- [ ] **Step 4: Run tests — should pass**

```bash
python -m pytest tests/test_window.py -v
```

Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add window.py tests/test_window.py
git commit -m "feat: floating subtitle window"
```

---

## Task 4: Speech recognizer

`SFSpeechRecognizer` only works on macOS with a microphone and system permission — it cannot be meaningfully unit tested in isolation. This task implements the module and verifies it loads correctly; real validation happens in Task 5 (manual test).

**Files:**
- Create: `recognizer.py`

- [ ] **Step 1: Write an import smoke test**

Add to `tests/test_window.py` (append to the file):

```python
def test_recognizer_imports():
    from recognizer import Recognizer
    assert Recognizer is not None
```

Run it to confirm it fails:
```bash
python -m pytest tests/test_window.py::test_recognizer_imports -v
```

Expected: ImportError

- [ ] **Step 2: Implement recognizer.py**

```python
import threading
from typing import Callable

import AVFoundation
import Speech


class Recognizer:
    """
    Wraps SFSpeechRecognizer + AVAudioEngine to stream mic audio for recognition.
    Calls on_result(text, is_final) from a background thread.
    """

    def __init__(self, on_result: Callable[[str, bool], None], locale: str = "en-US"):
        self._on_result = on_result
        self._locale = locale
        self._engine = None
        self._request = None
        self._task = None

    def start(self) -> None:
        locale = Speech.NSLocale.alloc().initWithLocaleIdentifier_(self._locale)
        recognizer = Speech.SFSpeechRecognizer.alloc().initWithLocale_(locale)

        if not recognizer.isAvailable():
            raise RuntimeError("SFSpeechRecognizer not available on this device.")

        self._request_permission(recognizer)

    def _request_permission(self, recognizer) -> None:
        Speech.SFSpeechRecognizer.requestAuthorization_(self._on_authorized)

    def _on_authorized(self, status) -> None:
        # SFSpeechRecognizerAuthorizationStatusAuthorized == 3
        if status != 3:
            raise RuntimeError(f"Microphone/speech permission denied (status={status}).")
        self._begin(Speech.SFSpeechRecognizer.alloc().initWithLocale_(
            Speech.NSLocale.alloc().initWithLocaleIdentifier_(self._locale)
        ))

    def _begin(self, recognizer) -> None:
        self._engine = AVFoundation.AVAudioEngine.alloc().init()
        input_node = self._engine.inputNode()
        fmt = input_node.outputFormatForBus_(0)

        self._request = Speech.SFSpeechAudioBufferRecognitionRequest.alloc().init()
        self._request.setShouldReportPartialResults_(True)

        def handle_result(result, error):
            if result is None:
                return
            text = result.bestTranscription().formattedString()
            is_final = result.isFinal()
            self._on_result(text, is_final)

        self._task = recognizer.recognitionTaskWithRequest_resultHandler_(
            self._request, handle_result
        )

        input_node.installTapOnBus_bufferSize_format_block_(
            0, 1024, fmt,
            lambda buf, _: self._request.appendAudioPCMBuffer_(buf)
        )

        self._engine.startAndReturnError_(None)

    def stop(self) -> None:
        if self._engine:
            self._engine.stop()
            self._engine.inputNode().removeTapOnBus_(0)
        if self._request:
            self._request.endAudio()
        if self._task:
            self._task.cancel()
```

- [ ] **Step 3: Run import smoke test — should pass**

```bash
python -m pytest tests/test_window.py::test_recognizer_imports -v
```

Expected: 1 passed

- [ ] **Step 4: Commit**

```bash
git add recognizer.py tests/test_window.py
git commit -m "feat: SFSpeechRecognizer wrapper"
```

---

## Task 5: Wire everything together in main.py

**Files:**
- Create: `main.py`

- [ ] **Step 1: Implement main.py**

```python
import tkinter as tk
from history import History
from window import SubtitleWindow
from recognizer import Recognizer


def main():
    root = tk.Tk()
    history = History(max_lines=3)
    window = SubtitleWindow(root)

    def on_result(text: str, is_final: bool) -> None:
        history.update(text, is_final)
        data = history.display()
        root.after(0, lambda: window.render(
            lines=data["lines"], partial=data["partial"]
        ))

    recognizer = Recognizer(on_result=on_result)
    recognizer.start()

    root.protocol("WM_DELETE_WINDOW", lambda: (recognizer.stop(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run all tests to make sure nothing is broken**

```bash
python -m pytest tests/ -v
```

Expected: all tests pass

- [ ] **Step 3: Manual test — launch the app**

```bash
python main.py
```

macOS will show a permission prompt for microphone and speech recognition — click Allow both.

Speak out loud and verify:
- Partial text appears as you speak
- Sentence locks in when you pause
- Old sentences gray out and scroll up
- Window stays on top of other apps
- Window is draggable
- × button closes the app

- [ ] **Step 4: Commit**

```bash
git add main.py
git commit -m "feat: wire recognizer, history, and window into main"
```

---

## Done

Run `python main.py` to launch. The app needs microphone + speech recognition permission on first run — macOS will prompt automatically.

To add Japanese support later: change `"en-US"` to `"ja-JP"` in `main.py`.
