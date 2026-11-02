# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

from typing import TYPE_CHECKING

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.capsule import Capsule
from tagstudio.qt.controllers.inset_frame import InsetFrame
from tagstudio.qt.views.styles.stylesheets import PAD

if TYPE_CHECKING:
    pass


class SearchPanelView(QVBoxLayout):
    def __init__(
        self,
        placeholder_text: str,
        create_text: str = "",
        is_chooser: bool = True,
        has_view_limit: bool = True,
        is_results_debossed: bool = False,
    ) -> None:
        self.is_chooser: bool = is_chooser
        super().__init__()
        self.setContentsMargins(PAD, 0, PAD, 0)

        # Limit container
        self.limit_container = QWidget()
        self.limit_layout = QHBoxLayout(self.limit_container)
        self.limit_layout.setContentsMargins(0, 0, 0, 0)
        self.limit_layout.setSpacing(PAD * 2)
        self.limit_layout.addStretch(1)
        self.limit_title = QLabel(Translations["home.search.view_limit"])
        self.limit_layout.addWidget(self.limit_title)
        self.limit_container.setHidden(not has_view_limit)
        self.addWidget(self.limit_container)

        # Limit dropdown
        self.limit_combobox = QComboBox()
        self.limit_layout.addWidget(self.limit_combobox)
        self.limit_layout.addStretch(1)
        self.limit_combobox.setEditable(False)

        # Search field
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText(placeholder_text)
        self.search_field.setObjectName("search_field")
        self.search_field.setMinimumSize(QSize(0, 32))
        self.addWidget(self.search_field)

        # Scroll area
        self.scroll_contents = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_contents)
        self.scroll_layout.setContentsMargins(PAD, 0, PAD, 0)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area = QScrollArea()
        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; }")
        self.scroll_area.setWidget(self.scroll_contents)
        # NOTE: setWidget() turns this on
        self.scroll_contents.setAutoFillBackground(False)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.results_layout: QVBoxLayout | None = None
        if is_results_debossed:
            results_box = InsetFrame()
            self.results_layout = QVBoxLayout(results_box)
            self.results_layout.setContentsMargins(PAD, PAD, 0, PAD)
            self.results_layout.addWidget(self.scroll_area)
            self.addWidget(results_box)
        else:
            self.addWidget(self.scroll_area)

        # Create button
        self.create_button = QPushButton(create_text)
        if not self.is_chooser:
            self.addWidget(self.create_button)

        # Create from query button
        self.create_from_query_button = Capsule(is_stretched=True, is_dashed=True)
