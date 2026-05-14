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
    # The confirmed line must remain visible in the last label slot
    assert w._labels[2].cget("text") == "confirmed sentence."
    # Partial must appear in the cursor label, not overwrite label[2]
    assert "still speaking" in w._cursor_label.cget("text")

def test_recognizer_imports():
    from recognizer import Recognizer
    assert Recognizer is not None
