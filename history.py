class History:
    def __init__(self, max_lines: int = 3):
        self.max_lines = max_lines
        self.lines: list[str] = []
        self.partial: str = ""

    def update(self, text: str, is_final: bool) -> None:
        if is_final:
            self.lines.append(text)
            if len(self.lines) > self.max_lines:
                self.lines.pop(0)
            self.partial = ""
        else:
            self.partial = text

    def display(self) -> dict:
        return {"lines": list(self.lines), "partial": self.partial}
