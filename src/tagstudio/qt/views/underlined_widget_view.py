# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget

from tagstudio.qt.views.stylesheets.stylesheets import widget_underline_style


class UnderlinedWidgetView(QVBoxLayout):
    def __init__(self, widget: QWidget) -> None:
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(3)
        self.setAlignment(Qt.AlignmentFlag.AlignTop)

        # HACK: I don't know why I can't just use a QFrame for the outline.
        # The styling and sizing only seems to work if it's something like a QPushButton.
        self.underline = QPushButton()
        self.underline.setFlat(True)
        self.underline.setDisabled(True)
        self.underline.setMaximumHeight(4)
        self.underline.setStyleSheet(widget_underline_style())

        self.addWidget(widget)
        self.addWidget(self.underline)
