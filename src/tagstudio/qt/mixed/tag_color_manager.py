# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Callable
from typing import TYPE_CHECKING, Any, override

import structlog
from PySide6 import QtGui
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from tagstudio.core.constants import RESERVED_NAMESPACE_PREFIX
from tagstudio.core.utils.types import unwrap
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.inset_frame import InsetFrame
from tagstudio.qt.controllers.modal import Modal
from tagstudio.qt.controllers.modal_content import ModalContent
from tagstudio.qt.controllers.tiles.color_data import ColorData
from tagstudio.qt.controllers.tiles.tile import Tile
from tagstudio.qt.mixed.build_namespace import BuildNamespacePanel
from tagstudio.qt.views.modal_view import ModalView

logger = structlog.get_logger(__name__)

if TYPE_CHECKING:
    from tagstudio.qt.qt_driver import QtDriver


# TODO: Split to use MVC guidelines.
class TagColorManager(ModalContent):
    create_namespace_modal: Modal | None = None

    def __init__(
        self,
        driver: QtDriver,
    ):
        super().__init__()
        self.driver = driver
        self.lib = driver.lib
        self.is_initialized = False
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_layout.setContentsMargins(3, 3, 3, 3)
        self.scroll_layout.setSpacing(6)

        scroll_container: QWidget = InsetFrame()
        scroll_container.setObjectName("entryScrollContainer")
        scroll_container.setLayout(self.scroll_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("entryScrollArea")
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; }")
        self.scroll_area.setWidget(scroll_container)
        # NOTE: setWidget() turns this on
        scroll_container.setAutoFillBackground(False)

        self.setup_color_groups()

        self.new_namespace_button = QPushButton(Translations["namespace.new.button"])
        self.new_namespace_button.clicked.connect(self.create_namespace)

        self.root_layout.addWidget(self.scroll_area)

    @override
    def parent_post_init(self) -> None:
        window = self.window()
        window.setMinimumSize(800, 600)

        modal_view = window.layout()
        assert isinstance(modal_view, ModalView)
        # NOTE: Qt keeps only ResetRole on the left on every platform
        modal_view.button_box.addButton(
            self.new_namespace_button, QDialogButtonBox.ButtonRole.ResetRole
        )

        # self.import_pack_button = QPushButton()
        # Translations.translate_qobject(self.import_pack_button, "color.import_pack")
        # modal_view.button_box.addButton(
        #     self.import_pack_button, QDialogButtonBox.ButtonRole.ResetRole
        # )

    def setup_color_groups(self):
        all_default = True
        if self.driver.lib.engine:
            tiles = self.driver.main_window.inspector.containers
            for group, colors in self.driver.lib.tag_color_groups.items():
                if not group.startswith(RESERVED_NAMESPACE_PREFIX):
                    all_default = False
                color_data = ColorData(group, colors, self.driver.lib)
                color_data.updated.connect(
                    lambda: (
                        self.reset(),
                        self.setup_color_groups(),
                        ()
                        if len(self.driver.selection.selected) < 1
                        else tiles.update_from_entry(self.driver.selection.selected[0]),
                    )
                )
                tile = Tile(self.driver.lib.get_namespace_name(group))
                tile.set_inner_widget(color_data)
                if not group.startswith(RESERVED_NAMESPACE_PREFIX):
                    tile.set_remove_callback(
                        lambda checked=False, g=group: self.delete_namespace_dialog(
                            prompt=Translations["color.namespace.delete.prompt"],
                            callback=lambda namespace=g: (
                                self.lib.delete_namespace(namespace),
                                self.reset(),
                                self.setup_color_groups(),
                                ()
                                if len(self.driver.selection.selected) < 1
                                else tiles.update_from_entry(self.driver.selection.selected[0]),
                            ),
                        )
                    )

                self.scroll_layout.addWidget(tile)

            if all_default:
                ns_container = QWidget()
                ns_layout = QHBoxLayout(ns_container)
                ns_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                ns_layout.setContentsMargins(0, 18, 0, 18)
                namespace_prompt = QPushButton(Translations["namespace.new.prompt"])
                namespace_prompt.setFixedSize(namespace_prompt.sizeHint().width() + 8, 24)
                namespace_prompt.clicked.connect(self.create_namespace)
                ns_layout.addWidget(namespace_prompt)
                self.scroll_layout.addWidget(ns_container)

            self.is_initialized = True

    def reset(self):
        while self.scroll_layout.count():
            item = unwrap(self.scroll_layout.itemAt(0))
            widget = unwrap(item.widget())
            self.scroll_layout.removeWidget(widget)
            widget.deleteLater()
        self.is_initialized = False

    def create_namespace(self):
        build_namespace_panel = BuildNamespacePanel(self.lib)

        self.create_namespace_modal = Modal(
            build_namespace_panel,
            Translations["namespace.create.title"],
            is_savable=True,
        )

        self.create_namespace_modal.saved.connect(
            lambda: (
                self.lib.add_namespace(build_namespace_panel.build_namespace()),
                self.reset(),
                self.setup_color_groups(),
            )
        )

        self.create_namespace_modal.show()

    def delete_namespace_dialog(self, prompt: str, callback: Callable[..., Any]) -> None:  # pyright: ignore[reportExplicitAny]
        message_box = QMessageBox()
        message_box.setText(prompt)
        message_box.setWindowTitle(Translations["color.namespace.delete.title"])
        message_box.setIcon(QMessageBox.Icon.Warning)
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
        callback()

    @override
    def showEvent(self, event: QtGui.QShowEvent) -> None:
        if not self.is_initialized:
            self.setup_color_groups()
        return super().showEvent(event)
