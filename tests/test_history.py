from history import History

def test_starts_empty():
    h = History(max_lines=3)
    assert h.lines == []
    assert h.partial == ""

def test_partial_update():
    h = History(max_lines=3)
    h.update("hello world", is_final=False)
    assert h.partial == "hello world"
    assert h.lines == []

def test_final_appends_to_lines():
    h = History(max_lines=3)
    h.update("first sentence.", is_final=True)
    assert h.lines == ["first sentence."]
    assert h.partial == ""

def test_max_lines_evicts_oldest():
    h = History(max_lines=3)
    for i in range(4):
        h.update(f"sentence {i}.", is_final=True)
    assert len(h.lines) == 3
    assert h.lines[0] == "sentence 1."
    assert h.lines[-1] == "sentence 3."

def test_display_returns_correct_structure():
    h = History(max_lines=3)
    h.update("one.", is_final=True)
    h.update("two.", is_final=True)
    h.update("in progress", is_final=False)
    d = h.display()
    assert d["lines"] == ["one.", "two."]
    assert d["partial"] == "in progress"
