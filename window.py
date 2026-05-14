import sys
import tkinter as tk

COLORS = {
    "bg":      "#0f0f14",
    "old":     "#3d3d3d",
    "mid":     "#626262",
    "current": "#ffffff",
    "accent":  "#6c8eff",
    "cursor":  "#8aabff",
    "hl_bg":   "#1e2848",
    "dot_r":   "#ff5f56",
    "dot_y":   "#ffbd2e",
    "dot_g":   "#27c93f",
}

FONT_SIZE_DEFAULT = 12
FONT_SIZE_MIN = 10
FONT_SIZE_MAX = 24

CANVAS_W   = 420
CANVAS_H   = 185
WRAP_W     = 370
PAD_X      = 26
BAR_X      = 14
TITLEBAR_H = 28

SLOTS_Y = [68, 112, 165]

SCROLL_RESUME_MS = 3000  # ms of inactivity before returning to live mode


class SubtitleWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Live Captions")
        root.geometry(f"{CANVAS_W}x{CANVAS_H}+100+800")
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

        # Scroll state
        self._all_lines: list[str] = []
        self._scroll_offset = 0      # 0 = live; N = N lines back from end
        self._scroll_timer  = None   # after() ID for auto-resume
        self._last_lines:   list[str] = []
        self._last_partial: str = ""

        root.bind("<ButtonPress-1>", self._drag_start)
        root.bind("<B1-Motion>", self._drag_move)
        root.bind("<MouseWheel>", self._on_scroll)
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

        root.after(150, self._apply_rounded_corners)

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

        # Scroll position indicator (top-right, hidden by default)
        self._scroll_label = self._canvas.create_text(
            CANVAS_W - 12, DOT_Y,
            text="", fill=COLORS["accent"],
            font=("System", 9), anchor="e"
        )

        # ── Highlight background + accent bar ──────────────────────────
        hl_y1, hl_y2 = SLOTS_Y[2] - 28, SLOTS_Y[2] + 8
        self._hl_rect = self._canvas.create_rectangle(
            BAR_X + 4, hl_y1, CANVAS_W - 12, hl_y2,
            fill=COLORS["bg"], outline=""
        )
        self._bar = self._canvas.create_rectangle(
            BAR_X, hl_y1, BAR_X + 4, hl_y2,
            fill=COLORS["bg"], outline=""
        )

        # ── 3 subtitle text slots ──────────────────────────────────────
        self._line_ids = [
            self._canvas.create_text(PAD_X, SLOTS_Y[i], text="",
                                     width=WRAP_W,
                                     fill=[COLORS["old"], COLORS["mid"], COLORS["current"]][i],
                                     font=("System", self._font_size),
                                     anchor="sw")
            for i in range(3)
        ]

        # Keep for test compatibility — always empty now
        self._partial_id = self._canvas.create_text(
            0, 0, text="", width=0, fill=COLORS["bg"], anchor="sw"
        )

    # ── Scroll ─────────────────────────────────────────────────────────

    def _on_scroll(self, event) -> None:
        if event.delta > 0:   # scroll up → go further back
            max_offset = max(0, len(self._all_lines) - 1)
            self._scroll_offset = min(self._scroll_offset + 1, max_offset)
        else:                  # scroll down → approach live
            self._scroll_offset = max(0, self._scroll_offset - 1)

        if self._scroll_offset > 0:
            self._draw_scroll_view()
            self._reset_scroll_timer()
        else:
            self._resume_live()

    def _draw_scroll_view(self) -> None:
        lines = self._all_lines
        end   = max(0, len(lines) - self._scroll_offset + 1)
        start = max(0, end - 3)
        visible = lines[start:end]
        padded  = ([""] * (3 - len(visible)) + visible)[-3:]

        colors = [COLORS["old"], COLORS["mid"], COLORS["old"]]
        for i, (text, color) in enumerate(zip(padded, colors)):
            self._canvas.itemconfigure(self._line_ids[i], text=text, fill=color)

        # Hide live highlight
        self._canvas.itemconfigure(self._hl_rect, fill=COLORS["bg"])
        self._canvas.itemconfigure(self._bar,     fill=COLORS["bg"])

        # Show position: "↑ 3 ago" etc.
        label = f"↑ {self._scroll_offset} ago"
        self._canvas.itemconfigure(self._scroll_label, text=label)

    def _reset_scroll_timer(self) -> None:
        if self._scroll_timer:
            self.root.after_cancel(self._scroll_timer)
        self._scroll_timer = self.root.after(SCROLL_RESUME_MS, self._resume_live)

    def _resume_live(self) -> None:
        self._scroll_offset = 0
        self._scroll_timer  = None
        self._canvas.itemconfigure(self._scroll_label, text="")
        # Force immediate redraw so stale history content doesn't linger
        self.render(self._last_lines, self._last_partial)

    # ── Public API ─────────────────────────────────────────────────────

    def _apply_rounded_corners(self, radius: int = 12) -> None:
        try:
            from AppKit import NSApplication, NSColor
            app = NSApplication.sharedApplication()
            for win in app.windows():
                fr = win.frame()
                if (abs(fr.size.width - CANVAS_W) < 10
                        and abs(fr.size.height - CANVAS_H) < 40):
                    win.setOpaque_(False)
                    win.setBackgroundColor_(NSColor.clearColor())
                    cv = win.contentView()
                    cv.setWantsLayer_(True)
                    cv.layer().setCornerRadius_(radius)
                    cv.layer().setMasksToBounds_(True)
                    return
        except Exception as e:
            print(f"[Rounded] {e}", file=sys.stderr)

    def set_callbacks(self, on_toggle: callable, on_copy: callable) -> None:
        self._on_toggle = on_toggle
        self._on_copy = on_copy

    def render(self, lines: list[str], partial: str, all_lines: list[str] | None = None) -> None:
        if all_lines is not None:
            self._all_lines = all_lines
        self._last_lines   = lines
        self._last_partial = partial

        # Don't overwrite display while user is scrolling history
        if self._scroll_offset > 0:
            return

        # slot 2 = partial only; confirmed lines stay in slots 0-1
        history = ([""] * 2 + list(lines))[-2:]
        self._canvas.itemconfigure(self._line_ids[0], text=history[0], fill=COLORS["old"])
        self._canvas.itemconfigure(self._line_ids[1], text=history[1], fill=COLORS["mid"])
        self._canvas.itemconfigure(self._line_ids[2],
                                   text=partial, fill=COLORS["cursor"])

        if partial:
            self.root.update_idletasks()
            bbox = self._canvas.bbox(self._line_ids[2])
            if bbox:
                x1, y1, x2, y2 = bbox
                hl_top = max(y1 - 8, SLOTS_Y[1] + 10)
                hl_bot = y2 + 8
                self._canvas.coords(self._hl_rect,
                                    BAR_X + 4, hl_top, CANVAS_W - 12, hl_bot)
                self._canvas.coords(self._bar,
                                    BAR_X, hl_top, BAR_X + 4, hl_bot)
            self._canvas.itemconfigure(self._hl_rect, fill=COLORS["hl_bg"])
            self._canvas.itemconfigure(self._bar,     fill=COLORS["accent"])
        else:
            self._canvas.itemconfigure(self._hl_rect, fill=COLORS["bg"])
            self._canvas.itemconfigure(self._bar,     fill=COLORS["bg"])

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
        font = ("System", self._font_size)
        for lid in self._line_ids:
            self._canvas.itemconfigure(lid, font=font)

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
        if x < snap:                   x = 0
        elif x + CANVAS_W > sw - snap: x = sw - CANVAS_W
        if y < snap:                   y = 0
        elif y + CANVAS_H > sh - snap: y = sh - CANVAS_H
        self.root.geometry(f"+{x}+{y}")
