# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

"""A pagination widget created for TagStudio."""

from PySide6.QtCore import QObject, QSize, Signal
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QWidget,
)
from src.qt.helpers.qbutton_wrapper import QPushButtonWrapper


class Pagination(QWidget, QObject):
    """Widget containing controls for navigating between pages of items."""

    index = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.page_count: int = 0
        self.current_page_index: int = 0
        self.buffer_page_count: int = 4
        self.button_size = QSize(32, 24)

        # ------------ UI EXAMPLE --------------
        # [<] [1]...[3][4] [5] [6][7]...[42] [>]
        #            ^^^^ <-- 2 Buffer Pages
        # Center Page Number is Editable Text
        # --------------------------------------

        # [----------- ROOT LAYOUT ------------]
        self.setHidden(True)
        self.root_layout = QHBoxLayout(self)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        self.root_layout.setContentsMargins(0, 6, 0, 0)
        self.root_layout.setSpacing(3)

        # [<] ----------------------------------
        self.prev_button = QPushButtonWrapper()
        self.prev_button.setText("<")
        self.prev_button.setMinimumSize(self.button_size)
        self.prev_button.setMaximumSize(self.button_size)

        # --- [1] ------------------------------
        self.start_button = QPushButtonWrapper()
        self.start_button.setMinimumSize(self.button_size)
        self.start_button.setMaximumSize(self.button_size)

        # ------ ... ---------------------------
        self.start_ellipses = QLabel()
        self.start_ellipses.setMinimumSize(self.button_size)
        self.start_ellipses.setMaximumSize(self.button_size)
        self.start_ellipses.setText(". . .")

        # --------- [3][4] ---------------------
        self.start_buffer_container = QWidget()
        self.start_buffer_layout = QHBoxLayout(self.start_buffer_container)
        self.start_buffer_layout.setContentsMargins(0, 0, 0, 0)
        self.start_buffer_layout.setSpacing(3)

        # ---------------- [5] -----------------
        self.current_page_field = QLineEdit()
        self.current_page_field.setMinimumSize(self.button_size)
        self.current_page_field.setMaximumSize(self.button_size)
        self.validator = Validator(1, self.page_count)
        self.current_page_field.setValidator(self.validator)
        self.current_page_field.returnPressed.connect(
            lambda: self._goto_page(int(self.current_page_field.text()) - 1)
        )

        # -------------------- [6][7] ----------
        self.end_buffer_container = QWidget()
        self.end_buffer_layout = QHBoxLayout(self.end_buffer_container)
        self.end_buffer_layout.setContentsMargins(0, 0, 0, 0)
        self.end_buffer_layout.setSpacing(3)

        # -------------------------- ... -------
        self.end_ellipses = QLabel()
        self.end_ellipses.setMinimumSize(self.button_size)
        self.end_ellipses.setMaximumSize(self.button_size)
        self.end_ellipses.setText(". . .")

        # ----------------------------- [42] ---
        self.end_button = QPushButtonWrapper()
        self.end_button.setMinimumSize(self.button_size)
        self.end_button.setMaximumSize(self.button_size)

        # ---------------------------------- [>]
        self.next_button = QPushButtonWrapper()
        self.next_button.setText(">")
        self.next_button.setMinimumSize(self.button_size)
        self.next_button.setMaximumSize(self.button_size)

        # Add Widgets to Root Layout
        self.root_layout.addStretch(1)
        self.root_layout.addWidget(self.prev_button)
        self.root_layout.addWidget(self.start_button)
        self.root_layout.addWidget(self.start_ellipses)
        self.root_layout.addWidget(self.start_buffer_container)
        self.root_layout.addWidget(self.current_page_field)
        self.root_layout.addWidget(self.end_buffer_container)
        self.root_layout.addWidget(self.end_ellipses)
        self.root_layout.addWidget(self.end_button)
        self.root_layout.addWidget(self.next_button)
        self.root_layout.addStretch(1)

        self._populate_buffer_buttons()

    def update_buttons(self, page_count: int, index: int, emit: bool = True):
        # Guard
        if index < 0:
            raise ValueError("Negative index detected")

        for i in range(0, 10):
            if self.start_buffer_layout.itemAt(i):
                self.start_buffer_layout.itemAt(i).widget().setHidden(True)
            if self.end_buffer_layout.itemAt(i):
                self.end_buffer_layout.itemAt(i).widget().setHidden(True)

        end_page = page_count - 1
        if page_count <= 1:
            # Hide everything if there are only one or less pages.
            # [-------------- HIDDEN --------------]
            self.setHidden(True)

        elif page_count > 1:
            # Enable/Disable Next+Prev Buttons
            if index == 0:
                self.prev_button.setDisabled(True)
            else:
                self._assign_click(self.prev_button, index - 1)
                self.prev_button.setDisabled(False)

            if index == end_page:
                self.next_button.setDisabled(True)
            else:
                self._assign_click(self.next_button, index + 1)
                self.next_button.setDisabled(False)

            # Set Ellipses Sizes
            if 8 <= page_count <= 11:
                end_scale = max(1, page_count - index - 6)
                srt_scale = max(1, index - 5)
            elif page_count > 11:
                end_scale = max(1, 7 - index)
                srt_scale = max(1, (7 - (end_page - index)))

            if page_count >= 8:
                end_size = self.button_size.width() * end_scale + (3 * (end_scale - 1))
                srt_size = self.button_size.width() * srt_scale + (3 * (srt_scale - 1))
                self.end_ellipses.setMinimumWidth(end_size)
                self.end_ellipses.setMaximumWidth(end_size)
                self.start_ellipses.setMinimumWidth(srt_size)
                self.start_ellipses.setMaximumWidth(srt_size)

            # Enable/Disable Ellipses
            if index <= self.buffer_page_count + 1:
                self.start_ellipses.setHidden(True)
            else:
                self.start_ellipses.setHidden(False)
                self._assign_click(self.start_button, 0)
            if index >= (page_count - self.buffer_page_count - 2):
                self.end_ellipses.setHidden(True)
            else:
                self.end_ellipses.setHidden(False)

            # Hide/Unhide Start+End Buttons
            if index != 0:
                self.start_button.setText("1")
                self._assign_click(self.start_button, 0)
                self.start_button.setHidden(False)
            else:
                self.start_button.setHidden(True)
            if index != page_count - 1:
                self.end_button.setText(str(page_count))
                self._assign_click(self.end_button, page_count - 1)
                self.end_button.setHidden(False)
            else:
                self.end_button.setHidden(True)

            if index == 0 or index == 1:
                self.start_buffer_container.setHidden(True)
            else:
                self.start_buffer_container.setHidden(False)

            if index == page_count - 1 or index == page_count - 2:
                self.end_buffer_container.setHidden(True)
            else:
                self.end_buffer_container.setHidden(False)

            # Current Field and Buffer Pages
            sbc = 0
            for i in range(0, page_count):
                # Set Field
                if i == index:
                    if self.start_buffer_layout.itemAt(i):
                        self.start_buffer_layout.itemAt(i).widget().setHidden(True)
                    if self.end_buffer_layout.itemAt(i):
                        self.end_buffer_layout.itemAt(i).widget().setHidden(True)
                    sbc += 1
                    self.current_page_field.setText(str(i + 1))

                start_offset = max(0, (index - 4) - 4)
                end_offset = min(page_count - 1, (index + 4) - 4)
                if i < index:
                    if (i != 0) and i >= index - 4:
                        self.start_buffer_layout.itemAt(i - start_offset).widget().setHidden(False)
                        self.start_buffer_layout.itemAt(i - start_offset).widget().setText(  # type: ignore
                            str(i + 1)
                        )
                        self._assign_click(
                            self.start_buffer_layout.itemAt(i - start_offset).widget(),  # type: ignore
                            i,
                        )
                        sbc += 1
                    else:
                        if self.start_buffer_layout.itemAt(i):
                            self.start_buffer_layout.itemAt(i).widget().setHidden(True)
                        if self.end_buffer_layout.itemAt(i):
                            self.end_buffer_layout.itemAt(i).widget().setHidden(True)
                elif i > index:
                    if i != page_count - 1 and i <= index + 4:
                        self.end_buffer_layout.itemAt(i - end_offset).widget().setHidden(False)
                        self.end_buffer_layout.itemAt(i - end_offset).widget().setText(  # type: ignore
                            str(i + 1)
                        )
                        self._assign_click(
                            self.end_buffer_layout.itemAt(i - end_offset).widget(),  # type: ignore
                            i,
                        )
                    else:
                        if self.end_buffer_layout.itemAt(i):
                            self.end_buffer_layout.itemAt(i).widget().setHidden(True)
                        for j in range(0, self.buffer_page_count):
                            if self.end_buffer_layout.itemAt(i - end_offset + j):
                                self.end_buffer_layout.itemAt(
                                    i - end_offset + j
                                ).widget().setHidden(True)

                    if self.start_buffer_layout.itemAt(i - 1):
                        self.start_buffer_layout.itemAt(i - 1).widget().setHidden(True)

            self.setHidden(False)

        self.validator.setTop(page_count)
        if emit:
            self.index.emit(index)
        self.current_page_index = index
        self.page_count = page_count

    def _goto_page(self, index: int):
        self.update_buttons(self.page_count, index)

    def _assign_click(self, button: QPushButtonWrapper, index):
        if button.is_connected:
            button.clicked.disconnect()
        button.clicked.connect(lambda checked=False, i=index: self._goto_page(i))
        button.is_connected = True

    def _populate_buffer_buttons(self):
        for _ in range(max(self.buffer_page_count * 2, 5)):
            button = QPushButtonWrapper()
            button.setMinimumSize(self.button_size)
            button.setMaximumSize(self.button_size)
            button.setHidden(True)
            self.start_buffer_layout.addWidget(button)

            end_button = QPushButtonWrapper()
            end_button.setMinimumSize(self.button_size)
            end_button.setMaximumSize(self.button_size)
            end_button.setHidden(True)
            self.end_buffer_layout.addWidget(end_button)


class Validator(QIntValidator):
    def __init__(self, bottom: int, top: int, parent=None) -> None:
        super().__init__(bottom, top, parent)

    def fixup(self, input: str) -> str:
        input = input.strip("0")
        return super().fixup(str(self.top()) if input else "1")
