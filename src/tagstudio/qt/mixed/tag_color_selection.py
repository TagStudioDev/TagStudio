# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import structlog
from PySide6.QtCore import Qt
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

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import TagColorGroup
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.modal_content import ModalContent
from tagstudio.qt.views.layouts.flow_layout import FlowLayout
from tagstudio.qt.views.styles.stylesheets import HALF_PAD, INNER_RADIUS, PAD, SWATCH_SIZE, header
from tagstudio.qt.views.styles.tagstudio_style import set_color_group, set_swatch

logger = structlog.get_logger(__name__)


# TODO: Split to use MVC guidelines.
class TagColorSelection(ModalContent):
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
        self.scroll_layout.setContentsMargins(PAD, 0, PAD, 0)
        self.scroll_layout.setSpacing(HALF_PAD)

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
        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; }")
        self.scroll_area.setWidget(scroll_container)
        # Turned on by setWidget(), which paints a solid color behind the swatches
        scroll_container.setAutoFillBackground(False)
        self.root_layout.addWidget(self.scroll_area)

        # Add Widgets to Layout ================================================
        tag_color_groups = self.lib.tag_color_groups
        self.button_group = QButtonGroup(self)

        self.add_no_color_widget()
        self.scroll_layout.addSpacerItem(QSpacerItem(1, PAD))
        for group, colors in tag_color_groups.items():
            display_name: str = self.lib.get_namespace_name(group)
            self.scroll_layout.addWidget(QLabel(header(display_name if display_name else group, 4)))
            color_box_widget = QWidget()
            color_group_layout = FlowLayout()
            color_group_layout.setSpacing(1)
            color_group_layout.enable_grid_optimizations(value=False)
            color_group_layout.setContentsMargins(0, 0, 0, 0)
            color_box_widget.setLayout(color_group_layout)
            for color in colors:
                swatch = self._create_swatch(color)
                swatch.setObjectName(f"{color.namespace}.{color.slug}")
                swatch.setToolTip(color.name)
                swatch.clicked.connect(lambda checked=False, x=color: self.select_color(x))
                color_group_layout.addWidget(swatch)
                self.button_group.addButton(swatch)
            self.scroll_layout.addWidget(color_box_widget)
            self.scroll_layout.addSpacerItem(QSpacerItem(1, PAD))

    def add_no_color_widget(self):
        no_color_str: str = Translations["color.title.no_color"]
        self.scroll_layout.addWidget(QLabel(header(no_color_str, 4)))
        color_box_widget = QWidget()
        color_group_layout = FlowLayout()
        color_group_layout.setSpacing(1)
        color_group_layout.enable_grid_optimizations(value=False)
        color_group_layout.setContentsMargins(0, 0, 0, 0)
        color_box_widget.setLayout(color_group_layout)
        color = None
        swatch = self._create_swatch(color)
        swatch.setObjectName("None")
        swatch.setToolTip(no_color_str)
        swatch.clicked.connect(lambda checked=False, x=color: self.select_color(x))
        color_group_layout.addWidget(swatch)
        self.button_group.addButton(swatch)
        self.scroll_layout.addWidget(color_box_widget)

    @staticmethod
    def _create_swatch(color: TagColorGroup | None) -> QRadioButton:
        swatch = QRadioButton()
        swatch.setFixedSize(SWATCH_SIZE, SWATCH_SIZE)
        swatch.setProperty("radius", INNER_RADIUS)
        set_color_group(swatch, color)
        set_swatch(swatch)
        return swatch

    def select_color(self, color: TagColorGroup | None):
        self.selected_color = color

    def select_radio_button(self, color: TagColorGroup | None):
        object_name: str = "None" if not color else f"{color.namespace}.{color.slug}"
        for button in self.button_group.buttons():
            if button.objectName() == object_name:
                button.setChecked(True)
                self.select_color(color)
                break
