# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Iterable
from typing import TYPE_CHECKING

import structlog

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Tag
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.capsule import Capsule
from tagstudio.qt.mixed.field_widget import FieldWidget
from tagstudio.qt.views.layouts.flow_layout import FlowLayout

if TYPE_CHECKING:
    from tagstudio.qt.qt_driver import QtDriver

logger = structlog.get_logger(__name__)


# TODO: Use newer MVC style guidelines
class TagBoxWidgetView(FieldWidget):
    __lib: Library

    def __init__(self, title: str, driver: QtDriver) -> None:
        super().__init__(title)
        self.__lib = driver.lib

        self.__root_layout = FlowLayout()
        self.__root_layout.enable_grid_optimizations(value=False)
        self.__root_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__root_layout)

    def set_tags(self, tags: Iterable[Tag], partial_tag_ids: set[int] | None = None) -> None:
        tags_ = sorted(list(tags), key=lambda tag: self.__lib.tag_display_name(tag))
        logger.info("[TagBoxWidget] Tags:", tags=tags)
        while self.__root_layout.itemAt(0):
            self.__root_layout.takeAt(0).widget().deleteLater()  # pyright: ignore[reportOptionalMemberAccess]

        for tag in tags_:
            capsule = Capsule(
                has_edit=True, has_remove=True, search_label=Translations["tag.search_for_tag"]
            )
            capsule.set_text(self.__lib.tag_display_name(tag))
            capsule.set_color_group(tag.color)
            capsule.set_partial(bool(partial_tag_ids and tag.id in partial_tag_ids))
            capsule.on_click.connect(lambda t=tag: self._on_click(t))
            capsule.on_remove.connect(lambda t=tag: self._on_remove(t))
            capsule.on_edit.connect(lambda t=tag: self._on_edit(t))
            capsule.on_search.connect(lambda t=tag: self._on_search(t))
            self.__root_layout.addWidget(capsule)

    def _on_click(self, tag: Tag) -> None:
        raise NotImplementedError

    def _on_remove(self, tag: Tag) -> None:
        raise NotImplementedError

    def _on_edit(self, tag: Tag) -> None:
        raise NotImplementedError

    def _on_search(self, tag: Tag) -> None:
        raise NotImplementedError
