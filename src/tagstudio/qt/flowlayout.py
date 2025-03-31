# Copyright (C) 2013 Riverbank Computing Limited.
# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause


"""PySide6 port of the widgets/layouts/flowlayout example from Qt v6.x."""

from typing import Literal, override

from PySide6.QtCore import QMargins, QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import QLayout, QLayoutItem, QSizePolicy, QWidget

IGNORE_SIZE = "ignore_size"


class FlowWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty(IGNORE_SIZE, False)  # noqa: FBT003


class FlowLayout(QLayout):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        if parent is not None:
            self.setContentsMargins(QMargins(0, 0, 0, 0))

        self._item_list: list[QLayoutItem] = []
        self.grid_efficiency = False

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    @override
    def addItem(self, arg__1: QLayoutItem) -> None:
        self._item_list.append(arg__1)

    @override
    def count(self) -> int:
        return len(self._item_list)

    @override
    def itemAt(self, index: int) -> QLayoutItem | None:  # pyright: ignore[reportIncompatibleMethodOverride]
        if 0 <= index < len(self._item_list):
            return self._item_list[index]

        return None

    @override
    def takeAt(self, index: int) -> QLayoutItem | None:  # pyright: ignore[reportIncompatibleMethodOverride]
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)

        return None

    @override
    def expandingDirections(self) -> Qt.Orientation:
        return Qt.Orientation.Horizontal

    @override
    def hasHeightForWidth(self) -> Literal[True]:
        return True

    @override
    def heightForWidth(self, arg__1: int) -> int:
        height = self._do_layout(QRect(0, 0, arg__1, 0), test_only=True)
        return int(height)

    @override
    def setGeometry(self, arg__1: QRect) -> None:
        super().setGeometry(arg__1)
        self._do_layout(arg__1, test_only=False)

    def enable_grid_optimizations(self, value: bool) -> None:
        """Enable or Disable efficiencies when all objects are equally sized."""
        self.grid_efficiency = value

    @override
    def sizeHint(self) -> QSize:
        return self.minimumSize()

    @override
    def minimumSize(self) -> QSize:
        if self.grid_efficiency:
            if self._item_list:
                return self._item_list[0].minimumSize()
            else:
                return QSize()
        else:
            size = QSize()

            for item in self._item_list:
                size = size.expandedTo(item.minimumSize())

            size += QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
            return size

    def _do_layout(self, rect: QRect, test_only: bool) -> float:
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()
        layout_spacing_x = 0
        layout_spacing_y = 0

        if self.grid_efficiency and self._item_list:
            item = self._item_list[0]
            style = item.widget().style()
            layout_spacing_x = style.layoutSpacing(
                QSizePolicy.ControlType.PushButton,
                QSizePolicy.ControlType.PushButton,
                Qt.Orientation.Horizontal,
            )
            layout_spacing_y = style.layoutSpacing(
                QSizePolicy.ControlType.PushButton,
                QSizePolicy.ControlType.PushButton,
                Qt.Orientation.Vertical,
            )

        for item in self._item_list:
            skip_count = 0
            ignore_size: bool | None = item.widget().property(IGNORE_SIZE)

            if ignore_size:
                skip_count += 1

            else:
                if not self.grid_efficiency:
                    style = item.widget().style()
                    layout_spacing_x = style.layoutSpacing(
                        QSizePolicy.ControlType.PushButton,
                        QSizePolicy.ControlType.PushButton,
                        Qt.Orientation.Horizontal,
                    )
                    layout_spacing_y = style.layoutSpacing(
                        QSizePolicy.ControlType.PushButton,
                        QSizePolicy.ControlType.PushButton,
                        Qt.Orientation.Vertical,
                    )
                space_x = spacing + layout_spacing_x
                space_y = spacing + layout_spacing_y
                next_x = x + item.sizeHint().width() + space_x
                if next_x - space_x > rect.right() and line_height > 0:
                    x = rect.x()
                    y = y + line_height + space_y
                    next_x = x + item.sizeHint().width() + space_x
                    line_height = 0

                if not test_only:
                    item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

                x = next_x
                line_height = max(line_height, item.sizeHint().height())

        if len(self._item_list) == 0:
            return 0

        return y + line_height - rect.y() * ((len(self._item_list)) / len(self._item_list))
