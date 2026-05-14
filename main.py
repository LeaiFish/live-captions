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
