# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import structlog
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from tagstudio.qt.controllers.autofill_line_edit import AutofillLineEdit
from tagstudio.qt.controllers.horizontal_scroll_area import HorizontalScrollArea
from tagstudio.qt.views.styles.stylesheets import (
    autofill_line_edit_style,
    autofill_scroll_top_style,
)

logger = structlog.get_logger(__name__)


class SuggestBoxView(QVBoxLayout):
    def __init__(self, placeholder_text: str = "") -> None:
        super().__init__()

        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(0)

        scroll_area_style = """
        QScrollArea{
            background: transparent;
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
        self.scroll_area = HorizontalScrollArea()
        self.scroll_area.setStyleSheet(scroll_area_style)
        self.scroll_area.setViewportMargins(2, 0, 2, 0)
        scroll_area_container_layout.addWidget(self.scroll_area)
        self.scroll_area.setWidget(contents)
        search_bar_height = 28
        underline_padding = 7
        self.scroll_area.setMaximumHeight(search_bar_height + underline_padding)
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
        self.search_field.setMinimumHeight(search_bar_height)
        self.search_field.setPlaceholderText(placeholder_text)
        self.hint_icon_action = self.search_field.addAction(
            QPixmap(), AutofillLineEdit.ActionPosition.TrailingPosition
        )
        self.scroll_area.setFocusProxy(self.search_field)
        self.search_field.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.search_field.customContextMenuRequested.connect(self.search_field.show_action_menu)

        # Finalize Layout
        self.addWidget(scroll_area_container)
        self.addWidget(self.search_field)
