# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget

from tagstudio.qt.views.styles.stylesheets import HALF_PAD


class UnderlinedWidgetView(QVBoxLayout):
    UNDERLINE_PAD = HALF_PAD
    UNDERLINE_THICKNESS = HALF_PAD

    def __init__(self, widget: QWidget) -> None:
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(self.UNDERLINE_PAD)
        self.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.underline = QWidget()
        self.underline.setFixedHeight(self.UNDERLINE_THICKNESS)

        self.addWidget(widget)
        self.addWidget(self.underline)
