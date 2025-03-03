from PySide6.QtCore import QRect
from PySide6.QtWidgets import QPushButton, QWidget
from src.qt.flowlayout import FlowLayout


def test_flow_layout_happy_path(qtbot):
    class Window(QWidget):
        def __init__(self):
            super().__init__()

            self.flow_layout = FlowLayout(self)
            self.flow_layout.enable_grid_optimizations(value=True)
            self.flow_layout.addWidget(QPushButton("Short"))

    window = Window()
    assert window.flow_layout.count()
    assert window.flow_layout._do_layout(QRect(0, 0, 0, 0), test_only=False)
