from PySide6 import QtGui
from PySide6.QtWidgets import QTextEdit


class TextDisplayView(QTextEdit):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setReadOnly(True)
        self.setTabStopDistance(QtGui.QFontMetricsF(self.font()).horizontalAdvance(" ") * 4)
