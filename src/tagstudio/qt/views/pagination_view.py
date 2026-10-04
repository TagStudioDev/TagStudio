# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import override

from PIL import Image, ImageQt
from PySide6.QtCore import QSize
from PySide6.QtGui import QIntValidator, QPixmap, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.styles.color_overlay import auto_theme_overlay
from tagstudio.qt.views.styles.stylesheets import HALF_PAD, PAD


class PageValidator(QIntValidator):
    @override
    def fixup(self, input: str) -> str:
        input = input.strip("0")
        return super().fixup(str(self.top()) if input else "1")


class PaginationView(QHBoxLayout):
    # NOTE: UI Example:
    # [<] [1]...[3][4] [5] [6][7]...[42] [>]
    #            ^^^^ <-- 2 Buffer Pages
    # Center Page Number is Editable Text

    BUTTON_SIZE = QSize(32, 24)
    BUFFER_PAGE_COUNT = 4

    def __init__(self) -> None:
        super().__init__()
        self.setContentsMargins(0, PAD, 0, PAD)
        self.setSpacing(HALF_PAD)
        _rm = ResourceManager()

        # [<] ----------------------------------
        self.prev_button = QPushButton()
        prev_icon: Image.Image = auto_theme_overlay(_rm.bxs_left_arrow, use_alpha=False)
        self.prev_button.setIcon(QPixmap.fromImage(ImageQt.ImageQt(prev_icon)))
        self.prev_button.setIconSize(QSize(12, 12))
        self.prev_button.setMinimumSize(self.BUTTON_SIZE)
        self.prev_button.setMaximumSize(self.BUTTON_SIZE)

        # --- [1] ------------------------------
        self.start_button = QPushButton()
        self.start_button.setMinimumSize(self.BUTTON_SIZE)
        self.start_button.setMaximumSize(self.BUTTON_SIZE)

        # ------ ... ---------------------------
        self.start_ellipses = QLabel(". . .")
        self.start_ellipses.setMinimumSize(self.BUTTON_SIZE)
        self.start_ellipses.setMaximumSize(self.BUTTON_SIZE)

        # --------- [3][4] ---------------------
        self.start_buffer_container = QWidget()
        self.start_buffer_layout = QHBoxLayout(self.start_buffer_container)
        self.start_buffer_layout.setContentsMargins(0, 0, 0, 0)
        self.start_buffer_layout.setSpacing(3)

        # ---------------- [5] -----------------
        self.current_page_field = QLineEdit()
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
        self.end_ellipses = QLabel(". . .")
        self.end_ellipses.setMinimumSize(self.BUTTON_SIZE)
        self.end_ellipses.setMaximumSize(self.BUTTON_SIZE)

        # ----------------------------- [42] ---
        self.end_button = QPushButton()
        self.end_button.setMinimumSize(self.BUTTON_SIZE)
        self.end_button.setMaximumSize(self.BUTTON_SIZE)

        # ---------------------------------- [>]
        self.next_button = QPushButton()
        next_icon: Image.Image = auto_theme_overlay(_rm.bxs_right_arrow, use_alpha=False)
        self.next_button.setIcon(QPixmap.fromImage(ImageQt.ImageQt(next_icon)))
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

    def _populate_buffer_buttons(self) -> None:
        for _ in range(max(self.BUFFER_PAGE_COUNT * 2, 5)):
            button = QPushButton()
            button.setMinimumSize(self.BUTTON_SIZE)
            button.setMaximumSize(self.BUTTON_SIZE)
            button.setHidden(True)
            self.start_buffer_layout.addWidget(button)

            end_button = QPushButton()
            end_button.setMinimumSize(self.BUTTON_SIZE)
            end_button.setMaximumSize(self.BUTTON_SIZE)
            end_button.setHidden(True)
            self.end_buffer_layout.addWidget(end_button)
