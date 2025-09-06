# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PySide6.QtCore import QRect
from PySide6.QtWidgets import QPushButton, QWidget

from tagstudio.qt.view.layouts.flow_layout import FlowLayout


def test_flow_layout_happy_path():
    class Window(QWidget):
        def __init__(self):
            super().__init__()

            self.flow_layout = FlowLayout(self)
            self.flow_layout.enable_grid_optimizations(value=True)
            self.flow_layout.addWidget(QPushButton("Short"))

    window = Window()
    assert window.flow_layout.count()
    assert window.flow_layout._do_layout(QRect(0, 0, 0, 0), test_only=False)  # pyright: ignore[reportPrivateUsage]
