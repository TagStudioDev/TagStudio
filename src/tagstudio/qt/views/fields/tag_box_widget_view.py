# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from collections.abc import Iterable
from typing import TYPE_CHECKING

import structlog

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Tag
from tagstudio.qt.mixed.tag_widget import TagWidget
from tagstudio.qt.views.fields.field_widget import FieldWidget
from tagstudio.qt.views.layouts.flow_layout import FlowLayout

if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class TagBoxWidgetView(FieldWidget):
    __lib: Library

    def __init__(self, title: str, driver: "QtDriver") -> None:
        super().__init__(title)
        self.__lib = driver.lib

        self.__root_layout = FlowLayout()
        self.__root_layout.enable_grid_optimizations(value=False)
        self.__root_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__root_layout)

    def set_tags(self, tags: Iterable[Tag]) -> None:
        tags_ = sorted(list(tags), key=lambda tag: self.__lib.tag_display_name(tag))
        logger.info("[TagBoxWidget] Tags:", tags=tags)
        while self.__root_layout.itemAt(0):
            self.__root_layout.takeAt(0).widget().deleteLater()  # pyright: ignore[reportOptionalMemberAccess]

        for tag in tags_:
            tag_widget = TagWidget(tag, library=self.__lib, has_edit=True, has_remove=True)

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
