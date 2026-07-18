# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    pass

logger = structlog.get_logger(__name__)


class SuggestBoxView(QWidget):
    def __init__(self, is_chooser: bool) -> None:
        self.is_chooser: bool = is_chooser
        super().__init__()

        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(0)

        # Scroll area
        self.contents = QWidget()

        self.content_layout = QHBoxLayout(self.contents)
        self.content_layout.setSpacing(6)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area_container = QWidget()
        self.scroll_area_container.setObjectName("container")
        self.scroll_area_container_layout = QHBoxLayout(self.scroll_area_container)
        self.scroll_area_container_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area_container_layout.setSpacing(0)
        self.scroll_area_container.setStyleSheet(autofill_scroll_top_style("container"))

        # Search field
        self.search_field = AutofillLineEdit(self.scroll_area_container)
        self.search_field.setStyleSheet(autofill_line_edit_style())
        self.search_field.setObjectName("search_field")
        self.search_field.setMinimumHeight(28)

        # HACK: The transparent border allows for the focus border color to
        # still show above the tags at the edges. Sort of.
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

        self.scroll_area = QScrollArea()
        self.scroll_area.setFocusProxy(self.search_field)
        self.scroll_area.setStyleSheet(scroll_area_style)
        self.scroll_area_container_layout.addWidget(self.scroll_area)
        self.scroll_area.setWidget(self.contents)
        self.scroll_area.setMaximumHeight(28)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.verticalScrollBar().setEnabled(False)
        self.scroll_area.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self._root_layout.addWidget(self.scroll_area_container)
        self._root_layout.addWidget(self.search_field)
