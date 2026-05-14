import tkinter as tk
import pytest
from window import SubtitleWindow

@pytest.fixture
def root():
    r = tk.Tk()
    yield r
    r.destroy()

def test_window_creates_without_error(root):
    w = SubtitleWindow(root)
    assert w is not None

def test_render_updates_without_error(root):
    w = SubtitleWindow(root)
    w.render(lines=["first.", "second."], partial="in prog")
    root.update_idletasks()

def test_partial_does_not_overwrite_confirmed_line(root):
    w = SubtitleWindow(root)
    w.render(lines=["confirmed sentence."], partial="still speaking")
    root.update_idletasks()
    # Last confirmed line stays in slot 2
    text = w._canvas.itemcget(w._line_ids[2], "text")
    assert text == "confirmed sentence."
    # Partial appears in cursor slot
    partial_text = w._canvas.itemcget(w._partial_id, "text")
    assert "still speaking" in partial_text

def test_recognizer_imports():
    from recognizer import Recognizer
    assert Recognizer is not None
