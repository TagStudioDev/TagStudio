# Copyright (C) 2013 Riverbank Computing Limited.
# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

"""PySide6 port of the widgets/layouts/flowlayout example from Qt v6.x."""

from PySide6.QtCore import QMargins, QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import QLayout, QSizePolicy, QWidget


class FlowWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.ignore_size: bool = False


class FlowLayout(QLayout):
    def __init__(self, parent=None):
        super().__init__(parent)

        if parent is not None:
            self.setContentsMargins(QMargins(0, 0, 0, 0))

        self._item_list = []
        self.grid_efficiency = False

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):  # noqa: N802
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):  # noqa: N802
        if 0 <= index < len(self._item_list):
            return self._item_list[index]

        return None

    def takeAt(self, index):  # noqa: N802
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)

        return None

    def expandingDirections(self):  # noqa: N802
        return Qt.Orientation(0)

    def hasHeightForWidth(self):  # noqa: N802
        return True

    def heightForWidth(self, width):  # noqa: N802
        height = self._do_layout(QRect(0, 0, width, 0), test_only=True)
        return height

    def setGeometry(self, rect):  # noqa: N802
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def enable_grid_optimizations(self, value: bool):
        """Enable or Disable efficiencies when all objects are equally sized."""
        self.grid_efficiency = value

    def sizeHint(self):  # noqa: N802
        return self.minimumSize()

    def minimumSize(self):  # noqa: N802
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
        layout_spacing_x = None
        layout_spacing_y = None

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
            if issubclass(type(item.widget()), FlowWidget) and item.widget().ignore_size:
                skip_count += 1

            if (issubclass(type(item.widget()), FlowWidget) and not item.widget().ignore_size) or (
                not issubclass(type(item.widget()), FlowWidget)
            ):
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
