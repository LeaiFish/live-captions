import os
import queue
import sys
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from history import History
from window import SubtitleWindow
from recognizer import Recognizer


def _set_dock_icon() -> None:
    """Set Dock icon at runtime via AppKit, bypassing macOS unsigned-app template."""
    try:
        from AppKit import NSApplication, NSImage
        # When bundled, Resources sits two levels up from the executable
        exe_dir = Path(sys.executable).parent
        for candidate in [
            exe_dir.parent / "Resources" / "AppIcon.icns",
            Path(__file__).parent / "assets" / "AppIcon.icns",
        ]:
            if candidate.exists():
                img = NSImage.alloc().initWithContentsOfFile_(str(candidate))
                if img:
                    NSApplication.sharedApplication().setApplicationIconImage_(img)
                return
    except Exception:
        pass

PARTIAL_TIMEOUT = 1.5  # seconds of silence before auto-finalizing partial

# NSEvent key constants
NSKeyDownMask = 1 << 10
NSCommandKeyMask = 1 << 20
NSShiftKeyMask = 1 << 17


def setup_global_hotkeys(on_toggle: callable, on_copy: callable) -> None:
    """
    ⌘⇧H — toggle window visibility
    ⌘⇧C — copy last sentence to clipboard
    """
    try:
        from AppKit import NSEvent

        def handler(event):
            flags = event.modifierFlags()
            chars = event.charactersIgnoringModifiers()
            if (flags & NSCommandKeyMask) and (flags & NSShiftKeyMask):
                if chars == "h":
                    on_toggle()
                elif chars == "c":
                    on_copy()

        NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(NSKeyDownMask, handler)
    except Exception as e:
        print(f"[Hotkey] Could not register global hotkeys: {e}")


def main():
    root = tk.Tk()
    _set_dock_icon()  # must be after tk.Tk() so NSApplication is already initialised
    history = History(max_lines=3)
    window = SubtitleWindow(root)
    result_queue = queue.Queue()
    visible = [True]
    transcript: list[str] = []
    session_start = datetime.now().strftime("%Y-%m-%d_%H-%M")

    def toggle_visibility():
        visible[0] = not visible[0]
        if visible[0]:
            root.after(0, root.deiconify)
        else:
            root.after(0, root.withdraw)

    def copy_last_sentence() -> None:
        if transcript:
            root.after(0, lambda: (
                root.clipboard_clear(),
                root.clipboard_append(transcript[-1])
            ))

    LANGS = [("en-US", "EN"), ("zh-CN", "中")]
    lang_idx = [0]
    recognizer_ref: list = []

    def switch_lang() -> None:
        lang_idx[0] = (lang_idx[0] + 1) % len(LANGS)
        locale, label = LANGS[lang_idx[0]]
        window.set_lang_label(label)
        history.lines.clear()
        history.partial = ""
        last_partial[0] = ""
        last_partial_t[0] = 0.0
        if recognizer_ref:
            recognizer_ref[0].stop()
        new_rec = Recognizer(on_result=on_result, locale=locale)
        new_rec.start()
        recognizer_ref[0] = new_rec

    transcribing = [True]

    def toggle_transcription() -> None:
        if transcribing[0]:
            recognizer_ref[0].pause()
            transcribing[0] = False
            root.after(0, lambda: window.set_transcribing(False))
        else:
            recognizer_ref[0].resume()
            transcribing[0] = True
            root.after(0, lambda: window.set_transcribing(True))

    setup_global_hotkeys(toggle_visibility, copy_last_sentence)
    window.set_callbacks(on_toggle=toggle_visibility, on_copy=copy_last_sentence,
                         on_lang=switch_lang, on_quit=lambda: on_close(),
                         on_transcribe=toggle_transcription)
    window.set_lang_label("EN")

    def save_transcript() -> None:
        if not transcript:
            return
        from tkinter import filedialog
        default_name = f"captions-{session_start}.txt"
        default_dir = str(Path.home() / "Documents")
        path = filedialog.asksaveasfilename(
            title="Save transcript",
            initialfile=default_name,
            initialdir=default_dir,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        Path(path).write_text("\n".join(transcript), encoding="utf-8")
        print(f"[Transcript] Saved to {path}")

    last_partial: list[str]   = [""]
    last_partial_t: list[float] = [0.0]
    _running = [True]

    def on_result(text: str, is_final: bool) -> None:
        result_queue.put((text, is_final))

    def poll() -> None:
        if not _running[0]:
            return
        try:
            while True:
                text, is_final = result_queue.get_nowait()
                history.update(text, is_final)
                if is_final:
                    transcript.append(text)
                    last_partial[0] = ""
                    last_partial_t[0] = 0.0
                else:
                    if text != last_partial[0]:
                        last_partial[0] = text
                        last_partial_t[0] = time.monotonic()
                d = history.display()
                window.render(lines=d["lines"], partial=d["partial"], all_lines=transcript)
        except queue.Empty:
            pass

        # Auto-finalize if partial hasn't changed for PARTIAL_TIMEOUT seconds
        if (last_partial[0]
                and last_partial_t[0]
                and time.monotonic() - last_partial_t[0] > PARTIAL_TIMEOUT):
            text = last_partial[0]
            last_partial[0] = ""
            last_partial_t[0] = 0.0
            history.update(text, is_final=True)
            transcript.append(text)
            d = history.display()
            window.render(lines=d["lines"], partial=d["partial"], all_lines=transcript)
            # Restart the recognition task so its internal buffer starts fresh.
            # Without this, the next partial would include the just-finalized text
            # again (SFSpeechRecognizer accumulates across the lifetime of one task).
            recognizer_ref[0].restart_task()

        root.after(50, poll)

    recognizer = Recognizer(on_result=on_result)
    recognizer.start()
    recognizer_ref.append(recognizer)
    root.after(50, poll)

    def on_close():
        _running[0] = False
        recognizer_ref[0].stop()
        if transcript:
            from tkinter import messagebox
            if messagebox.askyesno("Save transcript?",
                                   f"Save {len(transcript)} sentence(s) to ~/Documents/captions/?"):
                save_transcript()
        root.destroy()
        os._exit(0)

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
