import tkinter as tk

COLORS = {
    "bg": "#0f0f14",
    "old": "#3a3a4a",
    "mid": "#6a6a7a",
    "current": "#ffffff",
    "accent": "#6c8eff",
    "cursor": "#6c8eff",
}
FONT_SIZE_DEFAULT = 12
FONT_SIZE_MIN = 10
FONT_SIZE_MAX = 24

CANVAS_W = 460
CANVAS_H = 200
WRAP_W = 420       # text wraps at this pixel width
PAD_X = 20        # left margin for text
BAR_X = 14        # x position of accent bar
# anchor="sw" — text grows UPWARD from these y positions
SLOTS_Y = [65, 120, 168]   # bottom-y of each slot (old, mid, current)
PARTIAL_Y = 192            # bottom-y of partial/cursor line


class SubtitleWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Live Captions")
        root.geometry(f"{CANVAS_W}x{CANVAS_H}+100+760")
        root.configure(bg=COLORS["bg"])
        root.wm_attributes("-topmost", True)
        self._alpha = 0.85
        root.wm_attributes("-alpha", self._alpha)
        try:
            root.overrideredirect(True)
        except Exception:
            pass

        self._drag_x = 0
        self._drag_y = 0
        self._font_size = FONT_SIZE_DEFAULT
        root.bind("<ButtonPress-1>", self._drag_start)
        root.bind("<B1-Motion>", self._drag_move)
        # ⌘= / ⌘- to adjust opacity
        root.bind("<Command-equal>", lambda _: self._adjust_alpha(0.1))
        root.bind("<Command-minus>", lambda _: self._adjust_alpha(-0.1))
        # ⌘↑ / ⌘↓ to adjust font size
        root.bind("<Command-Up>", lambda _: self._adjust_font(2))
        root.bind("<Command-Down>", lambda _: self._adjust_font(-2))
        # Right-click menu
        root.bind("<Button-2>", self._show_menu)
        root.bind("<Button-3>", self._show_menu)
        root.bind("<Control-Button-1>", self._show_menu)

        self._canvas = tk.Canvas(root, width=CANVAS_W, height=CANVAS_H,
                                 bg=COLORS["bg"], highlightthickness=0, bd=0)
        self._canvas.pack(fill="both", expand=True)

        # Close button
        self._canvas.create_text(CANVAS_W - 14, 8, text="×",
                                 fill=COLORS["old"], font=("System", 16),
                                 anchor="ne", tags="close")
        self._canvas.tag_bind("close", "<Button-1>", lambda _: root.destroy())

        # 3 subtitle text slots
        line_colors = [COLORS["old"], COLORS["mid"], COLORS["current"]]
        self._line_ids = [
            self._canvas.create_text(PAD_X, SLOTS_Y[i], text="",
                                     width=WRAP_W, fill=line_colors[i],
                                     font=("System", self._font_size), anchor="sw")
            for i in range(3)
        ]

        # Accent bar for current line (hidden by default)
        self._bar = self._canvas.create_rectangle(
            BAR_X, SLOTS_Y[2] - 36, BAR_X + 3, SLOTS_Y[2],
            fill=COLORS["bg"], outline=""
        )

        # Partial / cursor text
        self._partial_id = self._canvas.create_text(
            PAD_X, PARTIAL_Y, text="", width=WRAP_W,
            fill=COLORS["cursor"], font=("System", self._font_size + 1), anchor="sw"
        )

    def render(self, lines: list[str], partial: str) -> None:
        line_colors = [COLORS["old"], COLORS["mid"], COLORS["current"]]
        padded = ([""] * (3 - len(lines)) + lines)[-3:]

        for i, (text, color) in enumerate(zip(padded, line_colors)):
            self._canvas.itemconfigure(self._line_ids[i], text=text, fill=color)

        # Accent bar: show next to current line if it has content
        if padded[2]:
            self._canvas.itemconfigure(self._bar, fill=COLORS["accent"])
        else:
            self._canvas.itemconfigure(self._bar, fill=COLORS["bg"])

        self._canvas.itemconfigure(
            self._partial_id,
            text=("▋  " + partial) if partial else ""
        )

    def set_callbacks(self, on_toggle: callable, on_copy: callable) -> None:
        self._on_toggle = on_toggle
        self._on_copy = on_copy

    def _show_menu(self, event) -> None:
        menu = tk.Menu(self.root, tearoff=0,
                       bg="#1a1a2e", fg="#ffffff",
                       activebackground=COLORS["accent"],
                       activeforeground="#ffffff",
                       font=("System", 12))
        menu.add_command(label="Font Larger  ⌘↑", command=lambda: self._adjust_font(2))
        menu.add_command(label="Font Smaller  ⌘↓", command=lambda: self._adjust_font(-2))
        menu.add_separator()
        menu.add_command(label="More Opaque  ⌘=", command=lambda: self._adjust_alpha(0.1))
        menu.add_command(label="Less Opaque  ⌘-", command=lambda: self._adjust_alpha(-0.1))
        menu.add_separator()
        if hasattr(self, "_on_copy"):
            menu.add_command(label="Copy Last Sentence  ⌘⇧C", command=self._on_copy)
            menu.add_separator()
        if hasattr(self, "_on_toggle"):
            menu.add_command(label="Hide Window  ⌘⇧H", command=self._on_toggle)
        menu.add_command(label="Quit", command=self.root.destroy)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _adjust_font(self, delta: int) -> None:
        self._font_size = max(FONT_SIZE_MIN, min(FONT_SIZE_MAX, self._font_size + delta))
        font = ("System", self._font_size)
        font_cursor = ("System", self._font_size + 1)
        for lid in self._line_ids:
            self._canvas.itemconfigure(lid, font=font)
        self._canvas.itemconfigure(self._partial_id, font=font_cursor)

    def _adjust_alpha(self, delta: float) -> None:
        self._alpha = max(0.2, min(1.0, self._alpha + delta))
        self.root.wm_attributes("-alpha", self._alpha)

    def _drag_start(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _drag_move(self, event):
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")
