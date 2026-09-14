# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import typing
from collections.abc import Iterable
from typing import override

import structlog
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMessageBox, QPushButton

from tagstudio.core.constants import RESERVED_NAMESPACE_PREFIX
from tagstudio.core.library.alchemy.models import TagColorGroup
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.modal import Modal
from tagstudio.qt.controllers.tiles.tile_data import TileData
from tagstudio.qt.mixed.build_color import BuildColorPanel
from tagstudio.qt.mixed.tag_color_label import TagColorLabel
from tagstudio.qt.views.styles.stylesheets import add_button_style
from tagstudio.qt.views.tiles.color_data_view import ColorDataView

if typing.TYPE_CHECKING:
    from tagstudio.core.library.alchemy.library import Library

logger = structlog.get_logger(__name__)


class ColorData(TileData):
    """An inner widget for color names that goes in a Tile widget."""

    updated = Signal()

    def __init__(
        self,
        group: str,
        colors: list[TagColorGroup],
        library: Library,
    ) -> None:
        self.namespace = group
        self.colors: list[TagColorGroup] = colors
        self.lib: Library = library

        title = "" if not self.lib.engine else self.lib.get_namespace_name(group)
        super().__init__(title, ColorDataView())
        self.setObjectName("color_data")

        self.set_colors(self.colors)

    @override
    def layout(self) -> ColorDataView:
        return super().layout()  # pyright: ignore[reportReturnType]

    def set_colors(self, colors: Iterable[TagColorGroup]):
        colors_ = sorted(
            list(colors), key=lambda color: self.lib.get_namespace_name(color.namespace)
        )
        is_mutable = not self.namespace.startswith(RESERVED_NAMESPACE_PREFIX)
        max_width = 60
        color_widgets: list[TagColorLabel] = []

        layout = self.layout()
        while item := layout.takeAt(0):
            if widget := item.widget():
                widget.deleteLater()

        for color in colors_:
            color_widget = TagColorLabel(
                color=color,
                has_edit=is_mutable,
                has_remove=is_mutable,
                library=self.lib,
            )
            hint = color_widget.sizeHint().width()
            if hint > max_width:
                max_width = hint
            color_widget.on_click.connect(lambda c=color: self.edit_color(c))
            color_widget.on_remove.connect(lambda c=color: self.delete_color(c))

            color_widgets.append(color_widget)
            self.layout().addWidget(color_widget)

        for color_widget in color_widgets:
            color_widget.setFixedWidth(max_width)

        if is_mutable:
            add_button = QPushButton()
            add_button.setText("+")
            add_button.setFlat(True)
            add_button.setFixedSize(22, 22)
            add_button.setStyleSheet(add_button_style())
            add_button.clicked.connect(
                lambda: self.edit_color(
                    TagColorGroup(
                        slug="slug",
                        namespace=self.namespace,
                        name="Color",
                        primary="#FFFFFF",
                        secondary=None,
                    )
                )
            )
            self.layout().addWidget(add_button)

    def edit_color(self, color_group: TagColorGroup):
        build_color_panel = BuildColorPanel(self.lib, color_group)

        self.edit_modal = Modal(
            build_color_panel,
            "Edit Color",
            is_savable=True,
        )

        self.edit_modal.saved.connect(
            lambda: (self.lib.update_color(*build_color_panel.build_color()), self.updated.emit())
        )
        self.edit_modal.show()

    def delete_color(self, color_group: TagColorGroup):
        message_box = QMessageBox(
            QMessageBox.Icon.Warning,
            Translations["color.delete"],
            Translations.format("color.confirm_delete", color_name=color_group.name),
        )
        cancel_button = message_box.addButton(
            Translations["generic.cancel_alt"], QMessageBox.ButtonRole.RejectRole
        )
        message_box.addButton(
            Translations["generic.delete_alt"], QMessageBox.ButtonRole.DestructiveRole
        )
        message_box.setEscapeButton(cancel_button)
        result = message_box.exec_()
        logger.info(QMessageBox.ButtonRole.DestructiveRole.value)
        if result != QMessageBox.ButtonRole.ActionRole.value:
            return

        logger.info("[ColorData] Removing color", color=color_group)
        self.lib.delete_color(color_group)
        self.updated.emit()
