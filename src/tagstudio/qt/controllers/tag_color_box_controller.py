# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import typing

import structlog
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMessageBox

from tagstudio.core.constants import RESERVED_NAMESPACE_PREFIX
from tagstudio.core.library.alchemy.models import TagColorGroup
from tagstudio.qt.mixed.build_color import BuildColorPanel
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.panel_modal import PanelModal
from tagstudio.qt.views.tag_color_box_view import TagColorBoxWidgetView

if typing.TYPE_CHECKING:
    from tagstudio.core.library.alchemy.library import Library

logger = structlog.get_logger(__name__)


class TagColorBoxWidget(TagColorBoxWidgetView):
    updated = Signal()

    def __init__(
        self,
        group: str,
        colors: list["TagColorGroup"],
        library: "Library",
    ) -> None:
        self.namespace = group
        self.colors: list[TagColorGroup] = colors
        self.lib: Library = library

        title = "" if not self.lib.engine else self.lib.get_namespace_name(group)
        super().__init__(title)

        sorted_colors = sorted(
            list(self.colors), key=lambda color: self.lib.get_namespace_name(color.namespace)
        )
        is_mutable = not self.namespace.startswith(RESERVED_NAMESPACE_PREFIX)
        self.set_colors(sorted_colors, is_mutable)

    def _on_add_color(self):
        self._on_edit_color(
            TagColorGroup(
                slug="slug",
                namespace=self.namespace,
                name="Color",
                primary="#FFFFFF",
                secondary=None,
            )
        )

    def _on_edit_color(self, color_group: TagColorGroup):
        build_color_panel = BuildColorPanel(self.lib, color_group)

        edit_modal = PanelModal(
            build_color_panel,
            "Edit Color",
            has_save=True,
        )

        edit_modal.saved.connect(
            lambda: (self.lib.update_color(*build_color_panel.build_color()), self.updated.emit())  # type: ignore
        )
        edit_modal.show()

    def _on_delete_color(self, color_group: TagColorGroup):
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

        logger.info("[ColorBoxWidget] Removing color", color=color_group)
        self.lib.delete_color(color_group)
        self.updated.emit()
