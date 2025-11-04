from PySide6.QtWidgets import QLabel


class FilePropertyWidget(QLabel):
    """A widget representing a property of a file."""

    def __init__(self) -> None:
        super().__init__()

    def set_value(self, **kwargs) -> bool:
        raise NotImplementedError()
