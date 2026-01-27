from PySide6.QtWidgets import QWidget


class FieldWidget(QWidget):
    """A widget representing a field of an entry."""

    def __init__(self, title: str) -> None:
        super().__init__()
        self.title: str = title
