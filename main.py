import tkinter as tk
from history import History
from window import SubtitleWindow
from recognizer import Recognizer


def main():
    root = tk.Tk()
    history = History(max_lines=3)
    window = SubtitleWindow(root)

    def on_result(text: str, is_final: bool) -> None:
        def _update():
            history.update(text, is_final)
            d = history.display()
            window.render(lines=d["lines"], partial=d["partial"])
        root.after(0, _update)

    recognizer = Recognizer(on_result=on_result)
    recognizer.start()

    root.protocol("WM_DELETE_WINDOW", lambda: (recognizer.stop(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()
