# Copyright (C) 2013 Riverbank Computing Limited.
# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

"""PySide6 port of the widgets/layouts/flowlayout example from Qt v6.x"""

from PySide6.QtCore import Qt, QMargins, QPoint, QRect, QSize
from PySide6.QtWidgets import QLayout, QSizePolicy, QWidget


# class Window(QWidget):
#     def __init__(self):
#         super().__init__()

#         flow_layout = FlowLayout(self)
#         flow_layout.addWidget(QPushButton("Short"))
#         flow_layout.addWidget(QPushButton("Longer"))
#         flow_layout.addWidget(QPushButton("Different text"))
#         flow_layout.addWidget(QPushButton("More text"))
#         flow_layout.addWidget(QPushButton("Even longer button text"))

#         self.setWindowTitle("Flow Layout")


class FlowWidget(QWidget):
    """
    From what I understand:
    A generic Qt window.
    Please fix  my description
    """
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.ignore_size: bool = False


class FlowLayout(QLayout):
    """A generic Qt layout + the ability to keep track of the items in the layout."""
    def __init__(self, parent=None) -> None:
        # Initialize the parent class
        super().__init__(parent)

        # In case parent is set
        if parent is not None:
            # Set margins to 0.
            self.setContentsMargins(QMargins(0, 0, 0, 0))

        # Initialize the items list to nothing.
        self._item_list: list = []
        # Initialize grid efficiency to "False"
        self.grid_efficiency: bool = False

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item) -> None:
        """Add a given item to the list of items inside the layout."""
        self._item_list.append(item)

    def count(self) -> int:
        """Returns the amount of items in the layout"""
        return len(self._item_list)

    def itemAt(self, index: int):
        """Returns the item at a given index or False if the index is out of range."""
        # Try to get the value at index "index" (supports negative numbers).
        try:
            return self._item_list[index]
        except IndexError:
            return False

    def takeAt(self, index: int):
        """
        Acts like the pop instructions of a list.
        (Because that's exactly what it does but don't tell anyone.)
        """
        # Try to pop the value at index "index" (supports negative numbers).
        try:
            return self._item_list.pop(index)
        except IndexError:
            return False

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> True:
        # @Travis please explain this?
        return True

    def heightForWidth(self, width) -> int | float:
        height: int | float = self._do_layout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        """Sets size and position of the layout"""
        super(FlowLayout, self).setGeometry(rect)
        self._do_layout(rect, False)

    def setGridEfficiency(self, state: bool) -> None:
        """
        Enables or Disables efficiencies when all objects are equally sized.
        """
        self.grid_efficiency = state

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        """Calculates the minimum size of the layout based on the items and grid efficiency mode?"""
        # Check if grid efficiency is turned on.
        if self.grid_efficiency:
            # In case it is: Check if the layout's items list is *not* empty
            if self._item_list:
                # If it is not empty: Return the first object of the items list.
                return self._item_list[0].minimumSize()
            else:
                # If it is empty: Return?
                return QSize()
        # If grid efficiency is not on.
        else:
            # Initialize a size variable.
            size = QSize()

            # Per item in the items list
            for item in self._item_list:
                # Expand the size of the initial size variable
                # (Sets the size to the combined size of all the items in the list)
                size = size.expandedTo(item.minimumSize())

            size += QSize(
                2 * self.contentsMargins().top(), 2 * self.contentsMargins().top()
            )

            # Return the final size.
            return size

    def _do_layout(self, rect, test_only) -> int | float:

        #
        # Initialize variables.
        #
        x: int | float = rect.x()
        y: int | float = rect.y()
        line_height: int | float = 0
        spacing: int = self.spacing()
        # Declare for later use.
        item = None
        style = None
        layout_spacing_x = None
        layout_spacing_y = None
        #
        # End init.
        #

        # Check if the grid efficiency mode is on.
        if self.grid_efficiency:
            # If there are items in the list.
            if self._item_list:
                # Set the item variable to the first item in the list
                item = self._item_list[0]
                # Set the style variable to the style of the item's widget
                style = item.widget().style()
                # Set the x spacing
                layout_spacing_x = style.layoutSpacing(
                    QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal
                )
                # Set the y spacing
                layout_spacing_y = style.layoutSpacing(
                    QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical
                )
        for i, item in enumerate(self._item_list):
            # print(issubclass(type(item.widget()), FlowWidget))
            # print(item.widget().ignore_size)
            skip_count = 0
            if (
                issubclass(type(item.widget()), FlowWidget)
                and item.widget().ignore_size
            ):
                skip_count += 1

            if (
                issubclass(type(item.widget()), FlowWidget)
                and not item.widget().ignore_size
            ) or (not issubclass(type(item.widget()), FlowWidget)):
                # print(f'Item {i}')
                if not self.grid_efficiency:
                    style = item.widget().style()
                    layout_spacing_x = style.layoutSpacing(
                        QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal
                    )
                    layout_spacing_y = style.layoutSpacing(
                        QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical
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

        # print(y + line_height - rect.y() * ((len(self._item_list) - skip_count) / len(self._item_list)))
        # print(y + line_height - rect.y()) * ((len(self._item_list) - skip_count) / len(self._item_list))
        return (
            y + line_height - rect.y() * ((len(self._item_list)) / len(self._item_list))
        )


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     main_win = Window()
#     main_win.show()
#     sys.exit(app.exec())
