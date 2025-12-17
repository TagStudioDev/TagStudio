from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit, QVBoxLayout

from tagstudio.qt.views.panel_modal import PanelWidget


class AddUrlEntryPanel(PanelWidget):
    def __init__(self, text):
        super().__init__()

        self.setMinimumWidth(480)
        self.__root_layout = QVBoxLayout(self)
        self.__root_layout.setContentsMargins(6, 0, 6, 0)
        self.__root_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.__url_line = QLineEdit()
        self.__root_layout.addWidget(self.__url_line)

    def get_content(self) -> str:
        return self.__url_line.text()
