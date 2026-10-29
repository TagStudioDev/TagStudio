# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import override

from PySide6.QtCore import QSize
from PySide6.QtGui import QIntValidator, QPainter, QPaintEvent, QPalette, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStyle,
    QStyleOptionFrame,
    QWidget,
)

from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.styles.color_overlay import image_theme_color_overlay
from tagstudio.qt.views.styles.stylesheets import HALF_PAD, PAD, RADIUS


class PageValidator(QIntValidator):
    @override
    def fixup(self, input: str) -> str:
        input = input.strip("0")
        return super().fixup(str(self.top()) if input else "1")


class _PageField(QLineEdit):
    """The current page number, drawn to match the page buttons until it's edited.

    This exists because text isn't aligned the same way for buttons and line edits, so navigating
    pages doesn't cause the page numbers to jiggle as they switch between widgets.
    """

    @override
    def paintEvent(self, arg__1: QPaintEvent) -> None:
        if self.hasFocus():
            super().paintEvent(arg__1)
            return
        painter = QPainter(self)
        option = QStyleOptionFrame()
        self.initStyleOption(option)
        style = self.style()
        style.drawPrimitive(QStyle.PrimitiveElement.PE_PanelLineEdit, option, painter, self)
        style.drawItemText(
            painter,
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            self.palette(),
            self.isEnabled(),
            self.text(),
            QPalette.ColorRole.Text,
        )
        painter.end()


class PaginationView(QHBoxLayout):
    # NOTE: UI Example:
    # [<] [1]...[3][4] [5] [6][7]...[42] [>]
    #            ^^^^ <-- 2 Buffer Pages
    # Center Page Number is Editable Text

    BUTTON_SIZE = QSize(32, 24)
    BUFFER_PAGE_COUNT = 4

    def __init__(self) -> None:
        super().__init__()
        self.setContentsMargins(PAD, PAD, PAD, PAD)
        self.setSpacing(HALF_PAD)
        _rm = ResourceManager()

        # [<] ----------------------------------
        self.prev_button = QPushButton()
        self.prev_button.setIcon(image_theme_color_overlay(_rm.bxs_left_arrow, use_alpha=False))
        self.prev_button.setIconSize(QSize(12, 12))
        self.prev_button.setMinimumSize(self.BUTTON_SIZE)
        self.prev_button.setMaximumSize(self.BUTTON_SIZE)

        # --- [1] ------------------------------
        self.start_button = QPushButton()
        self.start_button.setMinimumSize(self.BUTTON_SIZE)
        self.start_button.setMaximumSize(self.BUTTON_SIZE)

        # ------ ... ---------------------------
        self.start_ellipses = QLabel("<b>. . .</b>")
        self.start_ellipses.setStyleSheet("padding-bottom: 1px;")
        self.start_ellipses.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        self.start_ellipses.setMinimumSize(self.BUTTON_SIZE)
        self.start_ellipses.setMaximumSize(self.BUTTON_SIZE)

        # --------- [3][4] ---------------------
        self.start_buffer_container = QWidget()
        self.start_buffer_layout = QHBoxLayout(self.start_buffer_container)
        self.start_buffer_layout.setContentsMargins(0, 0, 0, 0)
        self.start_buffer_layout.setSpacing(3)

        # ---------------- [5] -----------------
        self.current_page_field = _PageField()
        self.current_page_field.setMinimumSize(self.BUTTON_SIZE)
        self.current_page_field.setMaximumSize(self.BUTTON_SIZE)
        self.current_page_field.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.validator = PageValidator(1, 0)
        self.current_page_field.setValidator(self.validator)

        # -------------------- [6][7] ----------
        self.end_buffer_container = QWidget()
        self.end_buffer_layout = QHBoxLayout(self.end_buffer_container)
        self.end_buffer_layout.setContentsMargins(0, 0, 0, 0)
        self.end_buffer_layout.setSpacing(3)

        # -------------------------- ... -------
        self.end_ellipses = QLabel("<b>. . .</b>")
        self.end_ellipses.setStyleSheet("padding-bottom: 1px;")
        self.end_ellipses.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        self.end_ellipses.setMinimumSize(self.BUTTON_SIZE)
        self.end_ellipses.setMaximumSize(self.BUTTON_SIZE)

        # ----------------------------- [42] ---
        self.end_button = QPushButton()
        self.end_button.setMinimumSize(self.BUTTON_SIZE)
        self.end_button.setMaximumSize(self.BUTTON_SIZE)

        # ---------------------------------- [>]
        self.next_button = QPushButton()
        self.next_button.setIcon(image_theme_color_overlay(_rm.bxs_right_arrow, use_alpha=False))
        self.next_button.setIconSize(QSize(12, 12))
        self.next_button.setMinimumSize(self.BUTTON_SIZE)
        self.next_button.setMaximumSize(self.BUTTON_SIZE)

        # Finalize Layout
        self.addStretch(1)
        self.addWidget(self.prev_button)
        self.addWidget(self.start_button)
        self.addWidget(self.start_ellipses)
        self.addWidget(self.start_buffer_container)
        self.addWidget(self.current_page_field)
        self.addWidget(self.end_buffer_container)
        self.addWidget(self.end_ellipses)
        self.addWidget(self.end_button)
        self.addWidget(self.next_button)
        self.addStretch(1)
        self._populate_buffer_buttons()

        for button in (self.prev_button, self.start_button, self.end_button, self.next_button):
            button.setProperty("radius", RADIUS)

    def _populate_buffer_buttons(self) -> None:
        for _ in range(max(self.BUFFER_PAGE_COUNT * 2, 5)):
            button = QPushButton()
            button.setMinimumSize(self.BUTTON_SIZE)
            button.setMaximumSize(self.BUTTON_SIZE)
            button.setHidden(True)
            button.setProperty("radius", RADIUS)
            self.start_buffer_layout.addWidget(button)

            end_button = QPushButton()
            end_button.setMinimumSize(self.BUTTON_SIZE)
            end_button.setMaximumSize(self.BUTTON_SIZE)
            end_button.setHidden(True)
            end_button.setProperty("radius", RADIUS)
            self.end_buffer_layout.addWidget(end_button)
