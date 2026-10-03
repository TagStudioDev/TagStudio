# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout

from tagstudio.qt.views.styles.stylesheets import tag_remove_button_style, tag_style


class CapsuleView(QVBoxLayout):
    def __init__(self, padded: bool = False) -> None:
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)

        height = 28 if padded else 22
        self.button = QPushButton()
        self.button.setFlat(True)
        self.button.setMinimumSize(height * 2, height)
        self.button.setFixedHeight(height)

        inner_layout = QHBoxLayout(self.button)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.remove_button = QPushButton("–")
        self.remove_button.setFlat(True)
        self.remove_button.setFixedSize(height, height)
        self.remove_button.setHidden(True)
        inner_layout.addWidget(self.remove_button)

        self.addWidget(self.button)

    def set_colors(
        self,
        primary_color: QColor,
        border_color: QColor,
        highlight_color: QColor,
        text_color: QColor,
    ) -> None:
        self.button.setStyleSheet(
            tag_style(primary_color, text_color, border_color, highlight_color)
        )
        self.remove_button.setStyleSheet(
            tag_remove_button_style(primary_color, text_color, border_color, highlight_color)
        )
