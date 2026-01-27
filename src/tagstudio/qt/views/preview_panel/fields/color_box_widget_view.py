# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from collections.abc import Iterable
from typing import TYPE_CHECKING

import structlog
from PySide6.QtWidgets import QPushButton

from tagstudio.core.constants import RESERVED_NAMESPACE_PREFIX
from tagstudio.core.library.alchemy.enums import TagColorEnum
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import TagColorGroup
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.mixed.tag_color_label import TagColorLabel
from tagstudio.qt.models.palette import ColorType, get_tag_color
from tagstudio.qt.views.layouts.flow_layout import FlowLayout
from tagstudio.qt.views.preview_panel.fields.field_widget import FieldWidget

if TYPE_CHECKING:
    from tagstudio.core.library.alchemy.library import Library

logger = structlog.get_logger(__name__)

BUTTON_STYLE = f"""
    QPushButton{{
        background: {get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT)};
        color: {get_tag_color(ColorType.TEXT, TagColorEnum.DEFAULT)};
        font-weight: 600;
        border-color: {get_tag_color(ColorType.BORDER, TagColorEnum.DEFAULT)};
        border-radius: 6px;
        border-style: solid;
        border-width: 2px;
        padding-right: 4px;
        padding-bottom: 2px;
        padding-left: 4px;
        font-size: 15px;
    }}
    QPushButton::hover{{
        border-color: {get_tag_color(ColorType.LIGHT_ACCENT, TagColorEnum.DEFAULT)};
    }}
    QPushButton::pressed{{
        background: {get_tag_color(ColorType.LIGHT_ACCENT, TagColorEnum.DEFAULT)};
        color: {get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT)};
        border-color: {get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT)};
    }}
    QPushButton::focus{{
        border-color: {get_tag_color(ColorType.LIGHT_ACCENT, TagColorEnum.DEFAULT)};
        outline:none;
    }}
"""


class ColorBoxWidgetView(FieldWidget):
    """A widget holding a list of tag colors."""

    __lib: Library

    def __init__(self, group: str, colors: list["TagColorGroup"], library: "Library") -> None:
        self.namespace: str = group
        self.colors: list[TagColorGroup] = colors
        self.__lib: Library = library

        title: str = "" if not self.__lib.engine else self.__lib.get_namespace_name(group)
        super().__init__(title)

        # Color box
        self.setObjectName("colorBox")
        self.__root_layout = FlowLayout()
        self.__root_layout.enable_grid_optimizations(value=True)
        self.__root_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__root_layout)

        # Add button
        self.add_button_stylesheet = BUTTON_STYLE

        # Fill data
        self.set_colors(self.colors)

    def set_colors(self, colors: Iterable[TagColorGroup]) -> None:
        """Sets the colors the color box contains."""
        colors_ = sorted(
            list(colors), key=lambda color: self.__lib.get_namespace_name(color.namespace)
        )
        is_mutable = not self.namespace.startswith(RESERVED_NAMESPACE_PREFIX)
        max_width = 60

        while self.__root_layout.itemAt(0):
            unwrap(self.__root_layout.takeAt(0)).widget().deleteLater()

        color_widgets: list[TagColorLabel] = []

        for color in colors_:
            color_widget = TagColorLabel(
                color=color,
                has_edit=is_mutable,
                has_remove=is_mutable,
                library=self.__lib,
            )

            hint = color_widget.sizeHint().width()
            if hint > max_width:
                max_width = hint

            color_widget.on_click.connect(lambda c=color: self._on_edit_color(c))
            color_widget.on_remove.connect(lambda c=color: self._on_delete_color(c))

            color_widgets.append(color_widget)
            self.__root_layout.addWidget(color_widget)

        for color_widget in color_widgets:
            color_widget.setFixedWidth(max_width)

        if is_mutable:
            # Add button
            add_button = QPushButton()
            add_button.setText("+")
            add_button.setFlat(True)
            add_button.setFixedSize(22, 22)
            add_button.setStyleSheet(self.add_button_stylesheet)

            add_button.clicked.connect(
                lambda: self._on_edit_color(
                    TagColorGroup(
                        slug="slug",
                        namespace=self.namespace,
                        name="Color",
                        primary="#FFFFFF",
                        secondary=None,
                    )
                )
            )

            self.__root_layout.addWidget(add_button)

    def _on_edit_color(self, color_group: TagColorGroup) -> None:
        raise NotImplementedError

    def _on_delete_color(self, color_group: TagColorGroup) -> None:
        raise NotImplementedError
