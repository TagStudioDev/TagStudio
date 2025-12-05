from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit, QVBoxLayout

from tagstudio.qt.views.panel_modal import PanelWidget


class AddUrlEntryPanel(PanelWidget):
    def __init__(self, text):
        super().__init__()

        self.setMinimumWidth(480)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 0, 6, 0)
        self.root_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.url_line = QLineEdit()
        self.root_layout.addWidget(self.url_line)
