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

def test_partial_in_slot2_while_speaking(root):
    w = SubtitleWindow(root)
    w.render(lines=["confirmed sentence."], partial="still speaking")
    root.update_idletasks()
    # Partial in slot 2 while speaking
    assert w._canvas.itemcget(w._line_ids[2], "text") == "still speaking"
    # Confirmed line in slot 1
    assert w._canvas.itemcget(w._line_ids[1], "text") == "confirmed sentence."

def test_slot2_empty_when_silent(root):
    w = SubtitleWindow(root)
    w.render(lines=["confirmed sentence."], partial="")
    root.update_idletasks()
    # Slot 2 empty when not speaking — confirmed lines only in history slots
    assert w._canvas.itemcget(w._line_ids[2], "text") == ""
    assert w._canvas.itemcget(w._line_ids[1], "text") == "confirmed sentence."

def test_recognizer_imports():
    from recognizer import Recognizer
    assert Recognizer is not None
