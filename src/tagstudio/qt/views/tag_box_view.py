# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Iterable
from typing import TYPE_CHECKING

import structlog
from PySide6.QtWidgets import QLayoutItem

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Tag
from tagstudio.qt.mixed.tag_widget import TagWidget
from tagstudio.qt.views.field_widget_view import FieldWidgetView
from tagstudio.qt.views.layouts.flow_layout import FlowLayout

if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class TagBoxWidgetView(FieldWidgetView):
    """A widget that holds a list of tags."""

    def __init__(self, title: str, driver: "QtDriver") -> None:
        super().__init__(title)
        self.__lib: Library = driver.lib

        # Tag box
        self.setObjectName("tag_box")

        self.__root_layout = FlowLayout()
        self.__root_layout.enable_grid_optimizations(value=False)
        self.__root_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__root_layout)

    def set_tags(self, tags: Iterable[Tag]) -> None:
        """Sets the tags the tag box contains."""
        sorted_tags: list[Tag] = sorted(
            list(tags), key=lambda tag: self.__lib.tag_display_name(tag)
        )
        logger.info("[TagBoxWidget] Tags:", tags=tags)

        # Remove all tag widgets
        for i in reversed(range(self.__root_layout.count())):
            item: QLayoutItem | None = self.__root_layout.itemAt(i)
            if item is not None:
                item.widget().deleteLater()

        for tag in sorted_tags:
            tag_widget: TagWidget = TagWidget(
                tag, library=self.__lib, has_edit=True, has_remove=True
            )

            tag_widget.on_click.connect(lambda t=tag: self._on_click(t))
            tag_widget.on_remove.connect(lambda t=tag: self._on_remove(t))
            tag_widget.on_edit.connect(lambda t=tag: self._on_edit(t))

            tag_widget.search_for_tag_action.triggered.connect(
                lambda checked=False, t=tag: self._on_search(t)
            )

            self.__root_layout.addWidget(tag_widget)

    def _on_click(self, tag: Tag) -> None:
        raise NotImplementedError

    def _on_remove(self, tag: Tag) -> None:
        raise NotImplementedError

    def _on_edit(self, tag: Tag) -> None:
        raise NotImplementedError

    def _on_search(self, tag: Tag) -> None:
        raise NotImplementedError
