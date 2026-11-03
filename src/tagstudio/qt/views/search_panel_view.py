# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

from typing import TYPE_CHECKING

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from tagstudio.qt.controllers.capsule import Capsule
from tagstudio.qt.controllers.inset_frame import InsetFrame
from tagstudio.qt.views.styles.stylesheets import PAD
from tagstudio.qt.views.styles.tagstudio_style import set_track_side_inset
from tagstudio.qt.views.styles.widget_effects import DEBOSSED_OUTLINE_WIDTH

if TYPE_CHECKING:
    pass


class SearchPanelView(QVBoxLayout):
    def __init__(
        self,
        placeholder_text: str,
        create_text: str = "",
        is_chooser: bool = True,
    ) -> None:
        self.is_chooser: bool = is_chooser
        super().__init__()
        self.setContentsMargins(PAD, 0, PAD, 0)

        # Search field
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText(placeholder_text)
        self.search_field.setObjectName("search_field")
        self.search_field.setMinimumSize(QSize(0, 32))
        self.search_layout = QHBoxLayout()
        self.search_layout.addWidget(self.search_field)
        self.addLayout(self.search_layout)

        # Scroll area
        self.scroll_contents = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_contents)
        # Part of the scrolled content so rows scroll past it
        rows_top = PAD - DEBOSSED_OUTLINE_WIDTH
        self.scroll_layout.setContentsMargins(0, rows_top, 0, rows_top)
        self.scroll_layout.setSpacing(0)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # Reserves the rows' height
        self.rows_spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.scroll_layout.addItem(self.rows_spacer)
        self.scroll_area = QScrollArea()
        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; }")
        self.scroll_area.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.scroll_area.setWidget(self.scroll_contents)
        # NOTE: setWidget() turns this on
        self.scroll_contents.setAutoFillBackground(False)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        # Lets the results shrink away first as the panel shrinks so the field isn't squished
        self.scroll_area.setMinimumHeight(1)
        # Center the scroll bar between the capsules and the results box's edge
        set_track_side_inset(self.scroll_area.verticalScrollBar(), DEBOSSED_OUTLINE_WIDTH)
        results_box = InsetFrame()
        self.results_layout = QVBoxLayout(results_box)
        self.results_layout.setContentsMargins(
            PAD, DEBOSSED_OUTLINE_WIDTH, 0, DEBOSSED_OUTLINE_WIDTH
        )
        self.results_layout.addWidget(self.scroll_area)
        self.addWidget(results_box)

        # Create button
        self.create_button = QPushButton(create_text)
        if not self.is_chooser:
            self.addWidget(self.create_button)

        # Create from query button
        self.create_from_query_button = Capsule(is_stretched=True, is_dashed=True)
