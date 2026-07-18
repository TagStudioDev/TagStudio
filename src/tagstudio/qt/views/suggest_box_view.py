# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import structlog
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from tagstudio.qt.controllers.autofill_line_edit import AutofillLineEdit
from tagstudio.qt.views.stylesheets.stylesheets import (
    autofill_line_edit_style,
    autofill_scroll_top_style,
)

logger = structlog.get_logger(__name__)


class SuggestBoxView(QVBoxLayout):
    def __init__(self, placeholder_text: str = "") -> None:
        super().__init__()
        # Init layout
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(0)

        # HACK: The transparent border allows for the focus border color to
        # still show above the tags at the edges... sort of (overlaps on left when h-scrolling)
        scroll_area_style = """
        QScrollArea{
            background: transparent;
            border: solid;
            border-color: transparent;
            border-width: 0px 2px;
            padding-left: -2px;
            }
        QScrollArea > QWidget > QWidget{
            background: transparent;
            }
        """

        # Autocomplete ScrollArea
        contents = QWidget()
        self.content_layout = QHBoxLayout(contents)
        self.content_layout.setSpacing(6)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        scroll_area_container = QWidget()
        scroll_area_container.setObjectName("container")
        scroll_area_container_layout = QHBoxLayout(scroll_area_container)
        scroll_area_container_layout.setContentsMargins(0, 0, 0, 0)
        scroll_area_container_layout.setSpacing(0)
        scroll_area_container.setStyleSheet(autofill_scroll_top_style("container"))
        self.scroll_area = QScrollArea()
        self.scroll_area.setStyleSheet(scroll_area_style)
        scroll_area_container_layout.addWidget(self.scroll_area)
        self.scroll_area.setWidget(contents)
        self.scroll_area.setMaximumHeight(28)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.verticalScrollBar().setEnabled(False)
        self.scroll_area.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        # Search Field
        self.search_field = AutofillLineEdit(scroll_area_container)
        self.search_field.setStyleSheet(autofill_line_edit_style())
        self.search_field.setObjectName("search_field")
        self.search_field.setMinimumHeight(28)
        self.search_field.setPlaceholderText(placeholder_text)
        self.scroll_area.setFocusProxy(self.search_field)

        # Finalize layout
        self.addWidget(scroll_area_container)
        self.addWidget(self.search_field)
