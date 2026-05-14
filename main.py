import queue
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from history import History
from window import SubtitleWindow
from recognizer import Recognizer

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

    setup_global_hotkeys(toggle_visibility, copy_last_sentence)
    window.set_callbacks(on_toggle=toggle_visibility, on_copy=copy_last_sentence)

    def save_transcript() -> None:
        if not transcript:
            return
        out_dir = Path.home() / "Documents" / "captions"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{session_start}.txt"
        out_file.write_text("\n".join(transcript), encoding="utf-8")
        print(f"[Transcript] Saved to {out_file}")

    last_partial: list[str]   = [""]
    last_partial_t: list[float] = [0.0]

    def on_result(text: str, is_final: bool) -> None:
        result_queue.put((text, is_final))

    def poll() -> None:
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

        root.after(50, poll)

    recognizer = Recognizer(on_result=on_result)
    recognizer.start()
    root.after(50, poll)

    def on_close():
        recognizer.stop()
        if transcript:
            from tkinter import messagebox
            if messagebox.askyesno("Save transcript?",
                                   f"Save {len(transcript)} sentence(s) to ~/Documents/captions/?"):
                save_transcript()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
