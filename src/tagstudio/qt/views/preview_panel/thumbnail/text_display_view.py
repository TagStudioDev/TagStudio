from PySide6 import QtGui
from PySide6.QtGui import QGuiApplication, Qt
from PySide6.QtWidgets import QTextEdit

from tagstudio.core.enums import Theme


class TextDisplayView(QTextEdit):
    """A widget for displaying a plaintext file."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.panel_bg_color = (
            Theme.COLOR_BG_DARK.value
            if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
            else Theme.COLOR_BG_LIGHT.value
        )

        self.setReadOnly(True)
        self.setTabStopDistance(QtGui.QFontMetricsF(self.font()).horizontalAdvance(" ") * 4)
        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        self.setStyleSheet(f"""
            QTextEdit{{
                background:{self.panel_bg_color};
                border-radius:6px;
            }}
        """)
