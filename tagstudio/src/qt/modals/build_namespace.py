# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from uuid import uuid4

import structlog
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)
from src.core.library import Library
from src.core.library.alchemy.library import ReservedNamespaceError, slugify
from src.core.library.alchemy.models import Namespace
from src.core.palette import ColorType, UiColor, get_ui_color
from src.qt.translations import Translations
from src.qt.widgets.panel import PanelWidget

logger = structlog.get_logger(__name__)


class BuildNamespacePanel(PanelWidget):
    on_edit = Signal(Namespace)

    def __init__(self, library: Library, namespace: Namespace | None = None):
        super().__init__()
        self.lib = library
        self.namespace: Namespace | None

        self.setMinimumSize(340, 240)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 0, 6, 0)
        self.root_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Name -----------------------------------------------------------------
        self.name_widget = QWidget()
        self.name_layout = QVBoxLayout(self.name_widget)
        self.name_layout.setStretch(1, 1)
        self.name_layout.setContentsMargins(0, 0, 0, 0)
        self.name_layout.setSpacing(0)
        self.name_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.name_title = QLabel()
        Translations.translate_qobject(self.name_title, "library_object.name")
        self.name_layout.addWidget(self.name_title)
        self.name_field = QLineEdit()
        self.name_field.setFixedHeight(24)
        self.name_field.textChanged.connect(self.on_text_changed)
        Translations.translate_with_setter(
            self.name_field.setPlaceholderText, "library_object.name_required"
        )
        self.name_layout.addWidget(self.name_field)

        # Slug -----------------------------------------------------------------
        self.slug_widget = QWidget()
        self.slug_layout = QVBoxLayout(self.slug_widget)
        self.slug_layout.setStretch(1, 1)
        self.slug_layout.setContentsMargins(0, 0, 0, 0)
        self.slug_layout.setSpacing(0)
        self.slug_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.slug_title = QLabel()
        Translations.translate_qobject(self.slug_title, "library_object.slug")
        self.slug_layout.addWidget(self.slug_title)
        self.slug_field = QLineEdit()
        self.slug_field.setFixedHeight(24)
        self.slug_field.textChanged.connect(self.on_text_changed)
        Translations.translate_with_setter(
            self.slug_field.setPlaceholderText, "library_object.slug_required"
        )
        self.slug_layout.addWidget(self.slug_field)

        # Add Widgets to Layout ================================================
        self.root_layout.addWidget(self.name_widget)
        self.root_layout.addWidget(self.slug_widget)

        self.set_namespace(namespace)

    def set_namespace(self, namespace: Namespace | None):
        logger.info("[BuildNamespacePanel] Setting Namespace", namespace=namespace)
        self.namespace = namespace

        if namespace:
            self.name_field.setText(namespace.name)
            self.slug_field.setText(namespace.namespace)
        else:
            self.name_field.setText("User Colors")
            self.slug_field.setText(f"user-{uuid4()}")

    def on_text_changed(self):
        is_name_empty = not self.name_field.text().strip()
        is_slug_empty = not self.slug_field.text().strip()
        is_invalid = not self.slug_field.text().strip()

        try:
            slugify(self.slug_field.text())
        except ReservedNamespaceError:
            is_invalid = True

        self.name_field.setStyleSheet(
            f"border: 1px solid {get_ui_color(ColorType.PRIMARY, UiColor.RED)}; border-radius: 2px"
            if is_name_empty
            else ""
        )

        self.slug_field.setStyleSheet(
            f"border: 1px solid {get_ui_color(ColorType.PRIMARY, UiColor.RED)}; border-radius: 2px"
            if is_slug_empty or is_invalid
            else ""
        )

        if self.panel_save_button is not None:
            self.panel_save_button.setDisabled(is_name_empty)

    def build_namespace(self) -> Namespace:
        name = self.name_field.text()
        slug_raw = self.slug_field.text()
        slug = slugify(slug_raw)

        namespace = Namespace(namespace=slug, name=name)

        logger.info("[BuildNamespacePanel]", slug=slug, name=name)
        return namespace

    def parent_post_init(self):
        self.setTabOrder(self.name_field, self.slug_field)
        self.name_field.selectAll()
        self.name_field.setFocus()
