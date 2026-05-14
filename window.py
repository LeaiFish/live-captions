import tkinter as tk

COLORS = {
    "bg":      "#0f0f14",
    "old":     "#3d3d3d",   # rgba(255,255,255,0.22) on dark
    "mid":     "#626262",   # rgba(255,255,255,0.38) on dark
    "current": "#ffffff",
    "accent":  "#6c8eff",
    "cursor":  "#6c8eff",
    "hl_bg":   "#1a1e30",   # rgba(108,142,255,0.12) blended on bg
    "dot_r":   "#ff5f56",
    "dot_y":   "#ffbd2e",
    "dot_g":   "#27c93f",
}

FONT_SIZE_DEFAULT = 12
FONT_SIZE_MIN = 10
FONT_SIZE_MAX = 24

CANVAS_W  = 460
CANVAS_H  = 228
WRAP_W    = 420
PAD_X     = 20
BAR_X     = 14
TITLEBAR_H = 28

# anchor="sw" — y is the BOTTOM of each text slot
SLOTS_Y   = [93, 148, 196]
PARTIAL_Y = 220


class SubtitleWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Live Captions")
        root.geometry(f"{CANVAS_W}x{CANVAS_H}+100+730")
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
        root.bind("<Command-equal>", lambda _: self._adjust_alpha(0.1))
        root.bind("<Command-minus>", lambda _: self._adjust_alpha(-0.1))
        root.bind("<Command-Up>",    lambda _: self._adjust_font(2))
        root.bind("<Command-Down>",  lambda _: self._adjust_font(-2))
        root.bind("<Button-2>",         self._show_menu)
        root.bind("<Button-3>",         self._show_menu)
        root.bind("<Control-Button-1>", self._show_menu)

        self._canvas = tk.Canvas(root, width=CANVAS_W, height=CANVAS_H,
                                 bg=COLORS["bg"], highlightthickness=0, bd=0)
        self._canvas.pack(fill="both", expand=True)

        # ── Title bar ──────────────────────────────────────────────────
        DOT_Y, DOT_R = TITLEBAR_H // 2, 5
        for i, (color, action) in enumerate([
            (COLORS["dot_r"], lambda _: root.destroy()),
            (COLORS["dot_y"], lambda _: None),
            (COLORS["dot_g"], lambda _: None),
        ]):
            x = 14 + i * 16
            dot = self._canvas.create_oval(x - DOT_R, DOT_Y - DOT_R,
                                           x + DOT_R, DOT_Y + DOT_R,
                                           fill=color, outline="")
            self._canvas.tag_bind(dot, "<Button-1>", action)

        self._canvas.create_text(CANVAS_W // 2, DOT_Y,
                                 text="🎙 Live Captions",
                                 fill="#3f3f50", font=("System", 10),
                                 anchor="center")

        # ── Current-line highlight background + accent bar ─────────────
        hl_y1, hl_y2 = SLOTS_Y[2] - 44, SLOTS_Y[2] + 6
        self._hl_rect = self._canvas.create_rectangle(
            BAR_X + 3, hl_y1, CANVAS_W - 10, hl_y2,
            fill=COLORS["bg"], outline=""
        )
        self._bar = self._canvas.create_rectangle(
            BAR_X, hl_y1, BAR_X + 3, hl_y2,
            fill=COLORS["bg"], outline=""
        )

        # ── 3 subtitle text slots ──────────────────────────────────────
        line_colors = [COLORS["old"], COLORS["mid"], COLORS["current"]]
        self._line_ids = [
            self._canvas.create_text(PAD_X, SLOTS_Y[i], text="",
                                     width=WRAP_W, fill=line_colors[i],
                                     font=("System", self._font_size),
                                     anchor="sw")
            for i in range(3)
        ]

        # ── Partial / cursor ───────────────────────────────────────────
        self._partial_id = self._canvas.create_text(
            PAD_X, PARTIAL_Y, text="", width=WRAP_W,
            fill=COLORS["cursor"], font=("System", self._font_size + 1),
            anchor="sw"
        )

    def set_callbacks(self, on_toggle: callable, on_copy: callable) -> None:
        self._on_toggle = on_toggle
        self._on_copy = on_copy

    def render(self, lines: list[str], partial: str) -> None:
        line_colors = [COLORS["old"], COLORS["mid"], COLORS["current"]]
        padded = ([""] * (3 - len(lines)) + lines)[-3:]

        for i, (text, color) in enumerate(zip(padded, line_colors)):
            self._canvas.itemconfigure(self._line_ids[i], text=text, fill=color)

        # Resize highlight to match actual current-line bbox
        if padded[2]:
            self.root.update_idletasks()
            bbox = self._canvas.bbox(self._line_ids[2])
            if bbox:
                x1, y1, x2, y2 = bbox
                pad = 6
                self._canvas.coords(self._hl_rect,
                                    BAR_X + 3, y1 - pad, CANVAS_W - 10, y2 + pad)
                self._canvas.coords(self._bar,
                                    BAR_X, y1 - pad, BAR_X + 3, y2 + pad)
            self._canvas.itemconfigure(self._hl_rect, fill=COLORS["hl_bg"])
            self._canvas.itemconfigure(self._bar,     fill=COLORS["accent"])
        else:
            self._canvas.itemconfigure(self._hl_rect, fill=COLORS["bg"])
            self._canvas.itemconfigure(self._bar,     fill=COLORS["bg"])

        self._canvas.itemconfigure(
            self._partial_id,
            text=("▋  " + partial) if partial else ""
        )

    def _show_menu(self, event) -> None:
        menu = tk.Menu(self.root, tearoff=0,
                       bg="#1a1a2e", fg="#ffffff",
                       activebackground=COLORS["accent"],
                       activeforeground="#ffffff",
                       font=("System", 12))
        menu.add_command(label="Font Larger  ⌘↑",  command=lambda: self._adjust_font(2))
        menu.add_command(label="Font Smaller  ⌘↓", command=lambda: self._adjust_font(-2))
        menu.add_separator()
        menu.add_command(label="More Opaque  ⌘=",  command=lambda: self._adjust_alpha(0.1))
        menu.add_command(label="Less Opaque  ⌘-",  command=lambda: self._adjust_alpha(-0.1))
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
        font        = ("System", self._font_size)
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
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        snap = 20
        if x < snap:                  x = 0
        elif x + CANVAS_W > sw - snap: x = sw - CANVAS_W
        if y < snap:                   y = 0
        elif y + CANVAS_H > sh - snap: y = sh - CANVAS_H
        self.root.geometry(f"+{x}+{y}")
