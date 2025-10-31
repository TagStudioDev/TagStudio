from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
import structlog
from PySide6.QtWidgets import QMessageBox

from tagstudio.core.library.alchemy.models import TagColorGroup
from tagstudio.qt.mixed.build_color import BuildColorPanel
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.fields.color_box_widget_view import ColorBoxWidgetView
from tagstudio.qt.views.panel_modal import PanelModal

if TYPE_CHECKING:
    from tagstudio.core.library.alchemy.library import Library

logger = structlog.get_logger(__name__)


class ColorBoxWidget(ColorBoxWidgetView):
    """A widget holding a list of tag colors."""

    on_update = Signal()

    def __init__(self, group: str, colors: list[TagColorGroup], library: "Library") -> None:
        super().__init__(group, colors, library)
        self.__lib: Library = library

    def _on_edit_color(self, color_group: TagColorGroup) -> None:
        build_color_panel = BuildColorPanel(self.__lib, color_group)

        edit_color_modal = PanelModal(
            build_color_panel,
            "Edit Color",
            has_save=True,
        )

        edit_color_modal.saved.connect(
            lambda: (self.__lib.update_color(*build_color_panel.build_color()), self.on_update.emit())
        )

        edit_color_modal.show()

    def _on_delete_color(self, color_group: TagColorGroup) -> None:
        # Dialogue box
        message_box = QMessageBox(
            QMessageBox.Icon.Warning,
            Translations["color.delete"],
            Translations.format("color.confirm_delete", color_name=color_group.name),
        )

        # Buttons
        cancel_button = message_box.addButton(
            Translations["generic.cancel_alt"], QMessageBox.ButtonRole.RejectRole
        )
        message_box.addButton(
            Translations["generic.delete_alt"], QMessageBox.ButtonRole.DestructiveRole
        )
        message_box.setEscapeButton(cancel_button)

        # Dialogue box result
        result = message_box.exec_()
        logger.info(QMessageBox.ButtonRole.DestructiveRole.value)

        if result != QMessageBox.ButtonRole.ActionRole.value:
            return

        logger.info("[ColorBoxWidget] Removing color", color=color_group)
        self.__lib.delete_color(color_group)
        self.on_update.emit()
