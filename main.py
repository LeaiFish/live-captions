import queue
import tkinter as tk
from datetime import datetime
from pathlib import Path
from history import History
from window import SubtitleWindow
from recognizer import Recognizer

# NSEvent key constants
NSKeyDownMask = 1 << 10
NSCommandKeyMask = 1 << 20
NSShiftKeyMask = 1 << 17


def setup_global_hotkey(callback):
    """Listen for ⌘⇧H globally to toggle window visibility."""
    try:
        from AppKit import NSEvent

        def handler(event):
            flags = event.modifierFlags()
            chars = event.charactersIgnoringModifiers()
            if (flags & NSCommandKeyMask) and (flags & NSShiftKeyMask) and chars == "h":
                callback()

        NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(NSKeyDownMask, handler)
    except Exception as e:
        print(f"[Hotkey] Could not register global hotkey: {e}")


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

    setup_global_hotkey(toggle_visibility)

    def save_transcript() -> None:
        if not transcript:
            return
        out_dir = Path.home() / "Documents" / "captions"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{session_start}.txt"
        out_file.write_text("\n".join(transcript), encoding="utf-8")
        print(f"[Transcript] Saved to {out_file}")

    def on_result(text: str, is_final: bool) -> None:
        result_queue.put((text, is_final))

    def poll() -> None:
        try:
            while True:
                text, is_final = result_queue.get_nowait()
                history.update(text, is_final)
                if is_final:
                    transcript.append(text)
                d = history.display()
                window.render(lines=d["lines"], partial=d["partial"])
        except queue.Empty:
            pass
        root.after(50, poll)

    recognizer = Recognizer(on_result=on_result)
    recognizer.start()
    root.after(50, poll)

    def on_close():
        recognizer.stop()
        save_transcript()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
