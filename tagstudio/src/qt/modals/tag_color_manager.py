# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from typing import TYPE_CHECKING, Callable, override

import structlog
from PySide6 import QtCore, QtGui
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from src.core.constants import RESERVED_NAMESPACE_PREFIX
from src.core.enums import Theme
from src.qt.modals.build_namespace import BuildNamespacePanel
from src.qt.translations import Translations
from src.qt.widgets.color_box import ColorBoxWidget
from src.qt.widgets.fields import FieldContainer
from src.qt.widgets.panel import PanelModal

logger = structlog.get_logger(__name__)

# Only import for type checking/autocompletion, will not be imported at runtime.
if TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver


class TagColorManager(QWidget):
    create_namespace_modal: PanelModal | None = None

    def __init__(
        self,
        driver: "QtDriver",
    ):
        super().__init__()
        self.driver = driver
        self.lib = driver.lib
        Translations.translate_with_setter(self.setWindowTitle, "color_manager.title")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(720, 540)
        self.is_initialized = False
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 6, 6, 6)

        panel_bg_color = (
            Theme.COLOR_BG_DARK.value
            if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
            else Theme.COLOR_BG_LIGHT.value
        )

        self.title_label = QLabel()
        self.title_label.setObjectName("titleLabel")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setText(f"<h3>{Translations["color_manager.title"]}</h3>")

        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_layout.setContentsMargins(3, 3, 3, 3)
        self.scroll_layout.setSpacing(0)

        scroll_container: QWidget = QWidget()
        scroll_container.setObjectName("entryScrollContainer")
        scroll_container.setLayout(self.scroll_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("entryScrollArea")
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.scroll_area.setStyleSheet(
            "QWidget#entryScrollContainer{" f"background:{panel_bg_color};" "border-radius:6px;" "}"
        )
        self.scroll_area.setWidget(scroll_container)

        self.setup_color_groups()

        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(6, 6, 6, 6)

        self.new_group_button = QPushButton()
        Translations.translate_qobject(self.new_group_button, "namespace.new.button")
        self.new_group_button.clicked.connect(self.create_namespace)
        self.button_layout.addWidget(self.new_group_button)

        # self.import_pack_button = QPushButton()
        # Translations.translate_qobject(self.import_pack_button, "color.import_pack")
        # self.button_layout.addWidget(self.import_pack_button)

        self.button_layout.addStretch(1)

        self.done_button = QPushButton()
        Translations.translate_qobject(self.done_button, "generic.done_alt")
        self.done_button.clicked.connect(self.hide)
        self.button_layout.addWidget(self.done_button)

        self.root_layout.addWidget(self.title_label)
        self.root_layout.addWidget(self.scroll_area)
        self.root_layout.addWidget(self.button_container)
        logger.info(self.root_layout.dumpObjectTree())

    def setup_color_groups(self):
        if self.driver.lib.engine:
            for group, colors in self.driver.lib.tag_color_groups.items():
                color_box = ColorBoxWidget(group, colors, self.driver.lib)
                color_box.updated.connect(
                    lambda: (
                        self.reset(),
                        self.setup_color_groups(),
                        ()
                        if len(self.driver.selected) < 1
                        else self.driver.preview_panel.fields.update_from_entry(
                            self.driver.selected[0], update_badges=False
                        ),
                    )
                )
                field_container = FieldContainer(self.driver.lib.get_namespace_name(group))
                field_container.set_inner_widget(color_box)
                if not group.startswith(RESERVED_NAMESPACE_PREFIX):
                    field_container.set_remove_callback(
                        lambda checked=False, g=group: self.remove_message_box(
                            prompt=Translations["color.namespace.delete.prompt"],
                            callback=lambda namespace=g: (
                                self.lib.delete_namespace(namespace),
                                self.reset(),
                                self.setup_color_groups(),
                                ()
                                if len(self.driver.selected) < 1
                                else self.driver.preview_panel.fields.update_from_entry(
                                    self.driver.selected[0], update_badges=False
                                ),
                            ),
                        )
                    )

                self.scroll_layout.addWidget(field_container)
            self.is_initialized = True

    def reset(self):
        while self.scroll_layout.count():
            widget = self.scroll_layout.itemAt(0).widget()
            self.scroll_layout.removeWidget(widget)
            widget.deleteLater()
        self.is_initialized = False

    def create_namespace(self):
        build_namespace_panel = BuildNamespacePanel(self.lib)

        self.create_namespace_modal = PanelModal(
            build_namespace_panel,
            Translations["namespace.create.title"],
            Translations["namespace.create.title"],
            has_save=True,
        )

        self.create_namespace_modal.saved.connect(
            lambda: (
                self.lib.add_namespace(build_namespace_panel.build_namespace()),
                self.reset(),
                self.setup_color_groups(),
            )
        )

        self.create_namespace_modal.show()

    def remove_message_box(self, prompt: str, callback: Callable) -> None:
        remove_mb = QMessageBox()
        remove_mb.setText(prompt)
        remove_mb.setWindowTitle(Translations["color.namespace.delete.title"])
        remove_mb.setIcon(QMessageBox.Icon.Warning)
        cancel_button = remove_mb.addButton(
            Translations["generic.cancel_alt"], QMessageBox.ButtonRole.DestructiveRole
        )
        remove_mb.addButton("&Remove", QMessageBox.ButtonRole.RejectRole)
        remove_mb.setDefaultButton(cancel_button)
        remove_mb.setEscapeButton(cancel_button)
        result = remove_mb.exec_()
        if result == QMessageBox.ButtonRole.ActionRole.value:
            callback()

    @override
    def showEvent(self, event: QtGui.QShowEvent) -> None:  # noqa N802
        if not self.is_initialized:
            self.setup_color_groups()
        return super().showEvent(event)

    @override
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # noqa N802
        if event.key() == QtCore.Qt.Key.Key_Escape:  # noqa SIM114
            self.done_button.click()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.done_button.click()
        return super().keyPressEvent(event)
