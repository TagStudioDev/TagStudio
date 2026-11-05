# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import structlog
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from tagstudio.qt.controllers.autofill_line_edit import AutofillLineEdit
from tagstudio.qt.controllers.horizontal_scroll_area import HorizontalScrollArea
from tagstudio.qt.views.capsule_view import CapsuleView
from tagstudio.qt.views.styles.stylesheets import HALF_PAD, MED_HEIGHT, PAD
from tagstudio.qt.views.styles.widget_effects import DEBOSSED_OUTLINE_WIDTH
from tagstudio.qt.views.underlined_widget_view import UnderlinedWidgetView

logger = structlog.get_logger(__name__)


class SuggestBoxView(QVBoxLayout):
    """A row of suggestions above a search field."""

    # A capsule with an underline below it
    ROW_HEIGHT = (
        CapsuleView.HEIGHT
        + UnderlinedWidgetView.UNDERLINE_PAD
        + UnderlinedWidgetView.UNDERLINE_THICKNESS
    )

    def __init__(self, placeholder_text: str = "") -> None:
        super().__init__()
        self.setSpacing(0)
        side_inset = PAD - DEBOSSED_OUTLINE_WIDTH

        # Suggestions
        contents = QWidget()
        self.content_layout = QHBoxLayout(contents)
        self.content_layout.setSpacing(HALF_PAD)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.content_layout.setContentsMargins(side_inset, 0, side_inset, 0)
        self.scroll_area = HorizontalScrollArea()
        self.scroll_area.setWidget(contents)
        self.scroll_area.viewport().setAutoFillBackground(False)
        contents.setAutoFillBackground(False)
        self.scroll_area.setFixedHeight(self.ROW_HEIGHT)
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.verticalScrollBar().setEnabled(False)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setViewportMargins(DEBOSSED_OUTLINE_WIDTH, 0, DEBOSSED_OUTLINE_WIDTH, 0)

        # Search Field
        self.search_field = AutofillLineEdit()
        self.search_field.setObjectName("search_field")
        self.search_field.setFrame(False)
        self.search_field.setFixedHeight(CapsuleView.HEIGHT)
        self.search_field.setContentsMargins(PAD, 0, PAD, 0)
        self.search_field.setStyleSheet("QLineEdit { background: transparent; }")
        self.search_field.setPlaceholderText(placeholder_text)
        self.hint_icon_action = self.search_field.addAction(
            QPixmap(), AutofillLineEdit.ActionPosition.TrailingPosition
        )
        self.scroll_area.setFocusProxy(self.search_field)
        self.search_field.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.search_field.customContextMenuRequested.connect(self.search_field.show_action_menu)

        # Finalize Layout
        self.addWidget(self.scroll_area)
        self.addWidget(self.search_field)
        self.set_suggestions_visible(False)

    def set_suggestions_visible(self, visible: bool) -> None:
        """Show the suggestion row or shrink to just the search field."""
        field_margin = (MED_HEIGHT - CapsuleView.HEIGHT) // 2
        top_margin = PAD if visible else field_margin
        self.setContentsMargins(0, top_margin, 0, field_margin)
        self.scroll_area.setHidden(not visible)
