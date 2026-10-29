# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import typing
from collections.abc import Iterable
from typing import override

import structlog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QMessageBox, QPushButton

from tagstudio.core.constants import RESERVED_NAMESPACE_PREFIX
from tagstudio.core.library.alchemy.models import TagColorGroup
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.capsule import Capsule
from tagstudio.qt.controllers.modal import Modal
from tagstudio.qt.controllers.tiles.tile_data import TileData
from tagstudio.qt.mixed.build_color import BuildColorPanel
from tagstudio.qt.views.styles.stylesheets import CAPSULE_HEIGHT
from tagstudio.qt.views.styles.tagstudio_style import set_color_group
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
        capsules: list[Capsule] = []

        layout = self.layout()
        while item := layout.takeAt(0):
            if widget := item.widget():
                widget.deleteLater()

        for color in colors_:
            capsule = Capsule(has_edit=is_mutable, has_remove=is_mutable)
            capsule.set_text(color.name)
            capsule.set_color_group(color)
            hint = capsule.sizeHint().width()
            if hint > max_width:
                max_width = hint
            if is_mutable:
                capsule.on_click.connect(lambda c=color: self.edit_color(c))
                capsule.on_edit.connect(lambda c=color: self.edit_color(c))
                capsule.on_remove.connect(lambda c=color: self.delete_color(c))
            else:
                capsule.setCursor(Qt.CursorShape.ArrowCursor)

            capsules.append(capsule)
            self.layout().addWidget(capsule)

        for capsule in capsules:
            capsule.setFixedWidth(max_width)

        if is_mutable:
            add_button = QPushButton()
            add_button.setText("+")
            add_button.setFixedSize(CAPSULE_HEIGHT, CAPSULE_HEIGHT)
            font = add_button.font()
            font.setWeight(QFont.Weight.DemiBold)
            font.setPixelSize(15)
            add_button.setFont(font)
            set_color_group(add_button, None)
            add_button.clicked.connect(
                lambda: self.edit_color(
                    TagColorGroup(
                        slug="slug",
                        namespace=self.namespace,
                        name=Translations["color.placeholder"],
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
            Translations["color.edit"],
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
        delete_button = message_box.addButton(
            Translations["generic.delete_alt"], QMessageBox.ButtonRole.AcceptRole
        )
        message_box.setEscapeButton(cancel_button)
        message_box.setDefaultButton(cancel_button)
        message_box.exec()
        if message_box.clickedButton() != delete_button:
            return

        logger.info("[ColorData] Removing color", color=color_group)
        self.lib.delete_color(color_group)
        self.updated.emit()
