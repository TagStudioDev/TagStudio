# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Iterable

import structlog
from PySide6.QtCore import Signal

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Tag
from tagstudio.qt.mixed.tag_widget import TagWidget
from tagstudio.qt.views.layouts.flow_layout import FlowLayout

logger = structlog.get_logger(__name__)


class TagDataView(FlowLayout):
    """The layout used for a TagData widget."""

    tag_clicked = Signal(Tag)
    tag_removed = Signal(Tag)
    tag_edited = Signal(Tag)
    tag_searched = Signal(Tag)

    def __init__(self, library: Library) -> None:
        super().__init__()
        self._lib = library
        self.enable_grid_optimizations(value=False)
        self.setContentsMargins(0, 0, 0, 0)

    def set_tags(self, tags: Iterable[Tag]) -> None:
        tags_ = sorted(list(tags), key=lambda tag: self._lib.tag_display_name(tag))
        logger.info("[TagData] Tags:", tags=tags)
        while self.itemAt(0):
            self.takeAt(0).widget().deleteLater()  # pyright: ignore[reportOptionalMemberAccess]

        for tag in tags_:
            tag_widget = TagWidget(tag, library=self._lib, has_edit=True, has_remove=True)
            tag_widget.on_click.connect(lambda t=tag: self.tag_clicked.emit(t))
            tag_widget.on_remove.connect(lambda t=tag: self.tag_removed.emit(t))
            tag_widget.on_edit.connect(lambda t=tag: self.tag_edited.emit(t))
            tag_widget.search_for_tag_action.triggered.connect(
                lambda checked=False, t=tag: self.tag_searched.emit(t)
            )
            self.addWidget(tag_widget)
