# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
)

from tagstudio.qt.controllers.capsule import Capsule
from tagstudio.qt.controllers.inset_scroll_box import InsetScrollBox


class SearchPanelView(QVBoxLayout):
    def __init__(
        self,
        placeholder_text: str,
        create_text: str = "",
        is_chooser: bool = True,
    ) -> None:
        self.is_chooser: bool = is_chooser
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)

        # Search field
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText(placeholder_text)
        self.search_field.setObjectName("search_field")
        self.search_field.setMinimumSize(QSize(0, 32))
        self.search_layout = QHBoxLayout()
        self.search_layout.addWidget(self.search_field)
        self.addLayout(self.search_layout)

        # Scroll area
        self.results_box = InsetScrollBox()
        results_box_view = self.results_box.layout()
        self.scroll_area = results_box_view.scroll_area  # Alias
        self.scroll_contents = results_box_view.scroll_contents  # Alias
        self.scroll_layout = results_box_view.scroll_layout  # Alias
        self.scroll_layout.setSpacing(0)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # Reserves the rows' height
        self.rows_spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.scroll_layout.addItem(self.rows_spacer)
        # Lets the results shrink away first as the panel shrinks so the field isn't squished
        self.scroll_area.setMinimumHeight(1)
        self.addWidget(self.results_box)

        # Create button
        self.create_button = QPushButton(create_text)
        if not self.is_chooser:
            self.addWidget(self.create_button)

        # Create from query button
        self.create_from_query_button = Capsule(is_stretched=True, is_dashed=True)
