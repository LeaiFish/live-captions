import queue
import tkinter as tk
from history import History
from window import SubtitleWindow
from recognizer import Recognizer


def main():
    root = tk.Tk()
    history = History(max_lines=3)
    window = SubtitleWindow(root)
    result_queue = queue.Queue()

    def on_result(text: str, is_final: bool) -> None:
        # Only enqueue — never call tkinter from the ObjC callback thread
        result_queue.put((text, is_final))

    def poll() -> None:
        try:
            while True:
                text, is_final = result_queue.get_nowait()
                history.update(text, is_final)
                d = history.display()
                window.render(lines=d["lines"], partial=d["partial"])
        except queue.Empty:
            pass
        root.after(50, poll)

    recognizer = Recognizer(on_result=on_result)
    recognizer.start()
    root.after(50, poll)

    root.protocol("WM_DELETE_WINDOW", lambda: (recognizer.stop(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()
