# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import structlog
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QButtonGroup,
    QLabel,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)
from src.core.library import Library
from src.core.library.alchemy.models import TagColorGroup
from src.qt.flowlayout import FlowLayout
from src.qt.widgets.panel import PanelWidget
from src.qt.widgets.tag_color_preview import (
    get_border_color,
    get_highlight_color,
    get_primary_color,
    get_text_color,
)

logger = structlog.get_logger(__name__)


class TagColorSelection(PanelWidget):
    def __init__(self, library: Library):
        super().__init__()
        self.lib = library
        self.selected_color: TagColorGroup | None = None

        self.setMinimumSize(400, 400)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 0, 6, 0)
        self.root_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Add Widgets to Layout ================================================
        tag_color_groups = self.lib.tag_color_groups
        self.button_group = QButtonGroup(self)

        self.add_no_color_widget()
        for group, colors in tag_color_groups.items():
            self.root_layout.addWidget(QLabel(f"<h3>{group}</h3>"))
            color_box_widget = QWidget()
            color_group_layout = FlowLayout()
            color_group_layout.setSpacing(4)
            color_group_layout.enable_grid_optimizations(value=False)
            color_group_layout.setContentsMargins(0, 0, 0, 0)
            color_box_widget.setLayout(color_group_layout)
            for color in colors:
                primary_color = get_primary_color(color)
                border_color = (
                    get_border_color(primary_color)
                    if not (color and color.secondary)
                    else (QColor(color.secondary))
                )
                highlight_color = get_highlight_color(
                    primary_color if not (color and color.secondary) else QColor(color.secondary)
                )
                text_color: QColor
                if color and color.secondary:
                    text_color = QColor(color.secondary)
                else:
                    text_color = get_text_color(primary_color, highlight_color)

                radio_button = QRadioButton()
                radio_button.setObjectName(f"{color.namespace}.{color.slug}")
                radio_button.setToolTip(color.name)
                radio_button.setFixedSize(24, 24)
                radio_button.setStyleSheet(
                    f"QRadioButton{{"
                    f"background: rgba{primary_color.toTuple()};"
                    f"color: rgba{text_color.toTuple()};"
                    f"border-color: rgba{border_color.toTuple()};"
                    f"border-radius: 3px;"
                    f"border-style:solid;"
                    f"border-width: 2px;"
                    f"}}"
                    f"QRadioButton::indicator{{"
                    f"width: 12px;"
                    f"height: 12px;"
                    f"border-radius: 1px;"
                    f"margin: 4px;"
                    f"}}"
                    f"QRadioButton::indicator:checked{{"
                    f"background: rgba{text_color.toTuple()};"
                    f"}}"
                    f"QRadioButton::hover{{"
                    f"border-color: rgba{highlight_color.toTuple()};"
                    f"}}"
                )
                radio_button.clicked.connect(lambda checked=False, x=color: self.select_color(x))
                color_group_layout.addWidget(radio_button)
                self.button_group.addButton(radio_button)
            self.root_layout.addWidget(color_box_widget)

    def add_no_color_widget(self):
        self.root_layout.addWidget(QLabel("<h3>No Color</h3>"))
        color_box_widget = QWidget()
        color_group_layout = FlowLayout()
        color_group_layout.setSpacing(4)
        color_group_layout.enable_grid_optimizations(value=False)
        color_group_layout.setContentsMargins(0, 0, 0, 0)
        color_box_widget.setLayout(color_group_layout)
        color = None
        primary_color = get_primary_color(color)
        border_color = get_border_color(primary_color)
        highlight_color = get_highlight_color(primary_color)
        text_color: QColor
        if color and color.secondary:
            text_color = QColor(color.secondary)
        else:
            text_color = get_text_color(primary_color, highlight_color)

        radio_button = QRadioButton()
        radio_button.setObjectName("None")
        radio_button.setToolTip("No Color")
        radio_button.setFixedSize(24, 24)
        radio_button.setStyleSheet(
            f"QRadioButton{{"
            f"background: rgba{primary_color.toTuple()};"
            f"color: rgba{text_color.toTuple()};"
            f"border-color: rgba{border_color.toTuple()};"
            f"border-radius: 3px;"
            f"border-style:solid;"
            f"border-width: 2px;"
            f"}}"
            f"QRadioButton::indicator{{"
            f"width: 12px;"
            f"height: 12px;"
            f"border-radius: 1px;"
            f"margin: 4px;"
            f"}}"
            f"QRadioButton::indicator:checked{{"
            f"background: rgba{text_color.toTuple()};"
            f"}}"
            f"QRadioButton::hover{{"
            f"border-color: rgba{highlight_color.toTuple()};"
            f"}}"
        )
        radio_button.clicked.connect(lambda checked=False, x=color: self.select_color(x))
        color_group_layout.addWidget(radio_button)
        self.button_group.addButton(radio_button)
        self.root_layout.addWidget(color_box_widget)

    def select_color(self, color: TagColorGroup):
        self.selected_color = color

    def select_radio_button(self, color: TagColorGroup | None):
        object_name: str = "None" if not color else f"{color.namespace}.{color.slug}"
        for button in self.button_group.buttons():
            if button.objectName() == object_name:
                button.setChecked(True)
                break
