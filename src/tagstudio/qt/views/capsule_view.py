# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout

from tagstudio.qt.views.styles.stylesheets import (
    CAPSULE_HEIGHT,
    capsule_remove_button_style,
    capsule_text_style,
    get_tag_border_color,
)


class CapsuleView(QVBoxLayout):
    # TODO: Don't hardcode values for style, but still use default from constants
    HEIGHT = CAPSULE_HEIGHT
    TEXT_BORDER = 2  # The text's transparent border from tag_style

    def __init__(self) -> None:
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)

        height = self.HEIGHT
        self.button = QPushButton()
        self.button.setFlat(True)
        self.button.setMinimumSize(height * 2, height)
        self.button.setFixedHeight(height)

        inner_layout = QHBoxLayout(self.button)
        inner_layout.setContentsMargins(1, 1, 1, 1)  # Shadow inset
        inner_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.remove_button = QPushButton("–")
        self.remove_button.setFlat(True)
        self.remove_button.setFixedSize(height - 2, height - 2)
        self.remove_button.setHidden(True)
        inner_layout.addWidget(self.remove_button)

        self.addWidget(self.button)

    def set_colors(
        self,
        primary_color: QColor,
        border_color: QColor | None,
        highlight_color: QColor,
        text_color: QColor,
        is_pill: bool,
        icon_shrink: int | None = None,
        is_stretched: bool = False,
    ) -> None:
        left_padding = None
        if icon_shrink is not None:
            left_padding = self.HEIGHT - self.TEXT_BORDER - icon_shrink // 2
        right_padding = left_padding if is_stretched else None
        self.button.setStyleSheet(
            capsule_text_style(text_color, primary_color, is_pill, left_padding, right_padding)
        )
        self.remove_button.setStyleSheet(
            capsule_remove_button_style(
                primary_color,
                text_color,
                border_color or get_tag_border_color(primary_color),
                highlight_color,
                radius=self.remove_button.width() // 2 if is_pill else None,
            )
        )
