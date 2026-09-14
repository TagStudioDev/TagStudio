# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Iterable

import structlog
from PySide6.QtCore import Signal

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Tag
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.capsule import Capsule
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
            capsule = Capsule(
                has_edit=True, has_remove=True, search_label=Translations["tag.search_for_tag"]
            )
            capsule.set_text(self._lib.tag_display_name(tag))
            capsule.set_color_group(tag.color)
            capsule.on_click.connect(lambda t=tag: self.tag_clicked.emit(t))
            capsule.on_remove.connect(lambda t=tag: self.tag_removed.emit(t))
            capsule.on_edit.connect(lambda t=tag: self.tag_edited.emit(t))
            capsule.on_search.connect(lambda t=tag: self.tag_searched.emit(t))
            self.addWidget(capsule)
