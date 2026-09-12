# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import override
from warnings import catch_warnings

from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from tagstudio.qt.views.pagination_view import PaginationView
from tagstudio.qt.views.styles.stylesheets import pagination_style


class Pagination(QWidget):
    HEIGHT = 36
    _RIGHT_MARGIN = 6
    _SCROLLBAR_WIDTH = 14

    index = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.page_count: int = 0
        self.current_page_index: int = 0

        self.setHidden(True)
        self.setObjectName("pagination")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.setFixedHeight(self.HEIGHT)
        self.setStyleSheet(pagination_style())

        self.view = PaginationView()
        self.setLayout(self.view)
        self._connect_callbacks()

        if parent is not None:
            parent.installEventFilter(self)
            self._sync_geometry()

    def _connect_callbacks(self) -> None:
        self.view.current_page_field.returnPressed.connect(
            lambda: self._goto_page(int(self.view.current_page_field.text()) - 1)
        )

    def update_buttons(self, page_count: int, index: int, emit: bool = True):
        if index < 0:
            raise ValueError("Negative index detected")

        view = self.view
        for i in range(0, 10):
            if button := self._get_button_at(view.start_buffer_layout, i):
                button.setHidden(True)
            if button := self._get_button_at(view.end_buffer_layout, i):
                button.setHidden(True)

        end_page = page_count - 1
        # Hide everything if there are only one or less pages.
        if page_count <= 1:
            self.setHidden(True)

        # Enable/Disable Next + Prev Buttons
        elif page_count > 1:
            if index == 0:
                view.prev_button.setDisabled(True)
            else:
                self._assign_click(view.prev_button, index - 1)
                view.prev_button.setDisabled(False)

            if index == end_page:
                view.next_button.setDisabled(True)
            else:
                self._assign_click(view.next_button, index + 1)
                view.next_button.setDisabled(False)

            # Set Ellipses Sizes
            if 8 <= page_count <= 11:
                end_scale = max(1, page_count - index - 6)
                start_scale = max(1, index - 5)
            elif page_count > 11:
                end_scale = max(1, 7 - index)
                start_scale = max(1, (7 - (end_page - index)))
            else:
                end_scale, start_scale = 1, 1

            if page_count >= 8:
                end_size = view.BUTTON_SIZE.width() * end_scale + (3 * (end_scale - 1))
                start_size = view.BUTTON_SIZE.width() * start_scale + (3 * (start_scale - 1))
                view.end_ellipses.setMinimumWidth(end_size)
                view.end_ellipses.setMaximumWidth(end_size)
                view.start_ellipses.setMinimumWidth(start_size)
                view.start_ellipses.setMaximumWidth(start_size)

            # Enable/Disable Ellipses
            if index <= view.BUFFER_PAGE_COUNT + 1:
                view.start_ellipses.setHidden(True)
            else:
                view.start_ellipses.setHidden(False)
                self._assign_click(view.start_button, 0)
            if index >= (page_count - view.BUFFER_PAGE_COUNT - 2):
                view.end_ellipses.setHidden(True)
            else:
                view.end_ellipses.setHidden(False)

            # Hide/Unhide Start + End Buttons
            if index != 0:
                view.start_button.setText("1")
                self._assign_click(view.start_button, 0)
                view.start_button.setHidden(False)
            else:
                view.start_button.setHidden(True)
            if index != page_count - 1:
                view.end_button.setText(str(page_count))
                self._assign_click(view.end_button, page_count - 1)
                view.end_button.setHidden(False)
            else:
                view.end_button.setHidden(True)

            if index == 0 or index == 1:
                view.start_buffer_container.setHidden(True)
            else:
                view.start_buffer_container.setHidden(False)

            if index == page_count - 1 or index == page_count - 2:
                view.end_buffer_container.setHidden(True)
            else:
                view.end_buffer_container.setHidden(False)

            # Current Field and Buffer Pages
            for i in range(0, page_count):
                # Set Field
                if i == index:
                    if button := self._get_button_at(view.start_buffer_layout, i):
                        button.setHidden(True)
                    if button := self._get_button_at(view.end_buffer_layout, i):
                        button.setHidden(True)
                    view.current_page_field.setText(str(i + 1))

                start_offset = max(0, (index - 4) - 4)
                end_offset = min(page_count - 1, (index + 4) - 4)
                if i < index:
                    if (i != 0) and i >= index - 4:
                        if button := self._get_button_at(
                            view.start_buffer_layout, i - start_offset
                        ):
                            button.setHidden(False)
                            button.setText(str(i + 1))
                            self._assign_click(button, i)
                    else:
                        if button := self._get_button_at(view.start_buffer_layout, i):
                            button.setHidden(True)
                        if button := self._get_button_at(view.end_buffer_layout, i):
                            button.setHidden(True)
                elif i > index:
                    if i != page_count - 1 and i <= index + 4:
                        if button := self._get_button_at(view.end_buffer_layout, i - end_offset):
                            button.setHidden(False)
                            button.setText(str(i + 1))
                            self._assign_click(button, i)
                    else:
                        if button := self._get_button_at(view.end_buffer_layout, i):
                            button.setHidden(True)
                        for j in range(0, view.BUFFER_PAGE_COUNT):
                            if button := self._get_button_at(
                                view.end_buffer_layout, i - end_offset + j
                            ):
                                button.setHidden(True)

                    if button := self._get_button_at(view.start_buffer_layout, i - 1):
                        button.setHidden(True)

            self.setHidden(False)
            self._sync_geometry()
            self.raise_()

        view.validator.setTop(page_count)
        if emit:
            self.index.emit(index)
        self.current_page_index = index
        self.page_count = page_count

    def _goto_page(self, index: int):
        self.update_buttons(self.page_count, index)

    def _assign_click(self, button: QPushButton, index: int):
        with catch_warnings(record=True):
            button.clicked.disconnect()
        button.clicked.connect(lambda checked=False, i=index: self._goto_page(i))

    @staticmethod
    def _get_button_at(layout: QHBoxLayout, index: int) -> QPushButton | None:
        """Safely return a button in a layout at a given index, if it exists."""
        item = layout.itemAt(index)
        widget = item.widget() if item else None
        return widget if isinstance(widget, QPushButton) else None

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self.parentWidget() and event.type() == QEvent.Type.Resize:
            self._sync_geometry()
        return super().eventFilter(watched, event)

    def _sync_geometry(self):
        parent = self.parentWidget()
        if parent is None:
            return
        # Stays out of the way of the entry view scrollbar
        right_inset = max(self._RIGHT_MARGIN, self._SCROLLBAR_WIDTH)
        width = max(0, parent.width() - right_inset)
        self.setGeometry(0, parent.height() - self.HEIGHT, width, self.HEIGHT)
