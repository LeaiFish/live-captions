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
        root.geometry("460x200+100+760")
        root.configure(bg=COLORS["bg"])
        root.wm_attributes("-topmost", True)
        try:
            root.overrideredirect(True)
        except Exception:
            pass

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

        self._texts: list[tk.Text] = []
        self._accent: list[tk.Frame] = []
        for _ in range(3):
            row = tk.Frame(self._frame, bg=COLORS["bg"])
            row.pack(fill="x", pady=2)
            bar = tk.Frame(row, width=3, bg=COLORS["bg"])
            bar.pack(side="left", fill="y", padx=(0, 6))
            txt = tk.Text(row, height=1, wrap="word",
                          bg=COLORS["bg"], fg=COLORS["old"],
                          font=FONT_SMALL, bd=0, highlightthickness=0,
                          relief="flat", state="disabled", cursor="arrow")
            txt.pack(side="left", fill="x", expand=True)
            self._texts.append(txt)
            self._accent.append(bar)

        self._cursor_label = tk.Label(self._frame, text="", bg=COLORS["bg"],
                                      fg=COLORS["cursor"], font=FONT, anchor="w")
        self._cursor_label.pack(fill="x", padx=(9, 0))

    def _set_text(self, txt: tk.Text, content: str, color: str) -> None:
        txt.configure(state="normal", fg=color)
        txt.delete("1.0", "end")
        if content:
            txt.insert("1.0", content)
            # Adjust height to fit wrapped content
            txt.configure(height=max(1, int(txt.index("end-1c").split(".")[0])))
        else:
            txt.configure(height=1)
        txt.configure(state="disabled")

    def render(self, lines: list[str], partial: str) -> None:
        color_map = [COLORS["old"], COLORS["mid"], COLORS["current"]]
        padded = ([""] * (3 - len(lines)) + lines)[-3:]
        for i, (txt, bar, text) in enumerate(zip(self._texts, self._accent, padded)):
            self._set_text(txt, text, color_map[i])
            is_current = (i == 2 and text)
            bar.configure(bg=COLORS["accent"] if is_current else COLORS["bg"])
        self._cursor_label.configure(text=("▋  " + partial) if partial else "")

    def _drag_start(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _drag_move(self, event):
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")
