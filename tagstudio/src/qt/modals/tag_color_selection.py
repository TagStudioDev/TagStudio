# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import structlog
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QLabel,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)
from src.core.library import Library
from src.core.library.alchemy.enums import TagColorEnum
from src.core.library.alchemy.models import TagColorGroup
from src.core.palette import ColorType, get_tag_color
from src.qt.flowlayout import FlowLayout
from src.qt.translations import Translations
from src.qt.widgets.panel import PanelWidget
from src.qt.widgets.tag import (
    get_border_color,
    get_highlight_color,
    get_text_color,
)

logger = structlog.get_logger(__name__)


class TagColorSelection(PanelWidget):
    def __init__(self, library: Library):
        super().__init__()
        self.lib = library
        self.selected_color: TagColorGroup | None = None

        self.setMinimumSize(308, 540)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_layout.setContentsMargins(6, 0, 6, 0)
        self.scroll_layout.setSpacing(3)

        scroll_container: QWidget = QWidget()
        scroll_container.setObjectName("entryScrollContainer")
        scroll_container.setLayout(self.scroll_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("entryScrollArea")
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidget(scroll_container)
        self.root_layout.addWidget(self.scroll_area)

        # Add Widgets to Layout ================================================
        tag_color_groups = self.lib.tag_color_groups
        self.button_group = QButtonGroup(self)

        self.add_no_color_widget()
        self.scroll_layout.addSpacerItem(QSpacerItem(1, 6))
        for group, colors in tag_color_groups.items():
            display_name: str = self.lib.get_namespace_name(group)
            self.scroll_layout.addWidget(
                QLabel(f"<h4>{display_name if display_name else group}</h4>")
            )
            color_box_widget = QWidget()
            color_group_layout = FlowLayout()
            color_group_layout.setSpacing(4)
            color_group_layout.enable_grid_optimizations(value=False)
            color_group_layout.setContentsMargins(0, 0, 0, 0)
            color_box_widget.setLayout(color_group_layout)
            for color in colors:
                primary_color = self._get_primary_color(color)
                border_color = (
                    get_border_color(primary_color)
                    if not (color and color.secondary and color.color_border)
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
                bottom_color: str = (
                    f"border-bottom-color: rgba{text_color.toTuple()};" if color.secondary else ""
                )
                radio_button.setStyleSheet(
                    f"QRadioButton{{"
                    f"background: rgba{primary_color.toTuple()};"
                    f"color: rgba{text_color.toTuple()};"
                    f"border-color: rgba{border_color.toTuple()};"
                    f"{bottom_color}"
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
                    f"QRadioButton::focus{{"
                    f"outline-style: solid;"
                    f"outline-width: 2px;"
                    f"outline-radius: 3px;"
                    f"outline-color: rgba{highlight_color.toTuple()};"
                    f"}}"
                )
                radio_button.clicked.connect(lambda checked=False, x=color: self.select_color(x))
                color_group_layout.addWidget(radio_button)
                self.button_group.addButton(radio_button)
            self.scroll_layout.addWidget(color_box_widget)
            self.scroll_layout.addSpacerItem(QSpacerItem(1, 6))

    def add_no_color_widget(self):
        no_color_str: str = Translations["color.title.no_color"]
        self.scroll_layout.addWidget(QLabel(f"<h4>{no_color_str}</h4>"))
        color_box_widget = QWidget()
        color_group_layout = FlowLayout()
        color_group_layout.setSpacing(4)
        color_group_layout.enable_grid_optimizations(value=False)
        color_group_layout.setContentsMargins(0, 0, 0, 0)
        color_box_widget.setLayout(color_group_layout)
        color = None
        primary_color = self._get_primary_color(color)
        border_color = get_border_color(primary_color)
        highlight_color = get_highlight_color(primary_color)
        text_color: QColor
        if color and color.secondary and color.color_border:
            text_color = QColor(color.secondary)
        else:
            text_color = get_text_color(primary_color, highlight_color)

        radio_button = QRadioButton()
        radio_button.setObjectName("None")  # NOTE: Internal use, no translation needed.
        radio_button.setToolTip(no_color_str)
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
            f"QRadioButton::focus{{"
            f"outline-style: solid;"
            f"outline-width: 2px;"
            f"outline-radius: 3px;"
            f"outline-color: rgba{highlight_color.toTuple()};"
            f"}}"
        )
        radio_button.clicked.connect(lambda checked=False, x=color: self.select_color(x))
        color_group_layout.addWidget(radio_button)
        self.button_group.addButton(radio_button)
        self.scroll_layout.addWidget(color_box_widget)

    def select_color(self, color: TagColorGroup | None):
        self.selected_color = color

    def select_radio_button(self, color: TagColorGroup | None):
        object_name: str = "None" if not color else f"{color.namespace}.{color.slug}"
        for button in self.button_group.buttons():
            if button.objectName() == object_name:
                button.setChecked(True)
                self.select_color(color)
                break

    def _get_primary_color(self, tag_color_group: TagColorGroup | None) -> QColor:
        primary_color = QColor(
            get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT)
            if not tag_color_group
            else tag_color_group.primary
        )
        return primary_color
