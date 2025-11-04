from PySide6.QtWidgets import QLabel


class FilePropertyWidget(QLabel):
    """A widget representing a property of a file."""

    def __init__(self) -> None:
        super().__init__()

        self.label_style = """
            QLabel{
                color: #FFFFFF;
                font-family: Oxanium;
                font-weight: bold;
                font-size: 12px;
            }
        """
        self.setStyleSheet(self.label_style)

    def set_value(self, **kwargs) -> bool:
        raise NotImplementedError()
