from PySide6.QtWidgets import QWidget


class FieldWidgetView(QWidget):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.title: str = title
