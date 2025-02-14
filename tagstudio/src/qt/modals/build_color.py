# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from uuid import uuid4

import structlog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from src.core import palette
from src.core.library import Library
from src.core.library.alchemy.enums import TagColorEnum
from src.core.library.alchemy.library import ReservedNamespaceError, slugify
from src.core.library.alchemy.models import TagColorGroup
from src.core.palette import ColorType, UiColor, get_ui_color
from src.qt.translations import Translations
from src.qt.widgets.panel import PanelWidget
from src.qt.widgets.tag import (
    get_border_color,
    get_highlight_color,
    get_text_color,
)
from src.qt.widgets.tag_color_preview import TagColorPreview

logger = structlog.get_logger(__name__)


class BuildColorPanel(PanelWidget):
    on_edit = Signal(TagColorGroup)

    def __init__(self, library: Library, color_group: TagColorGroup):
        super().__init__()
        self.lib = library
        self.color_group: TagColorGroup
        self.tag_color_namespace: str | None
        self.tag_color_slug: str | None
        self.disambiguation_id: int | None

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
        self.slug_field.setEnabled(False)
        self.slug_field.setFixedHeight(24)
        Translations.translate_with_setter(
            self.slug_field.setPlaceholderText, "library_object.slug_required"
        )
        self.slug_layout.addWidget(self.slug_field)

        # Primary --------------------------------------------------------------
        self.primary_widget = QWidget()
        self.primary_layout = QHBoxLayout(self.primary_widget)
        self.primary_layout.setStretch(1, 1)
        self.primary_layout.setContentsMargins(0, 0, 0, 0)
        self.primary_layout.setSpacing(6)
        self.primary_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.primary_title = QLabel()
        Translations.translate_qobject(self.primary_title, "color.primary")
        self.primary_layout.addWidget(self.primary_title)
        self.primary_button = QPushButton()
        self.primary_button.setMinimumSize(44, 22)
        self.primary_button.setMaximumHeight(22)
        self.edit_primary_modal = QColorDialog()
        self.primary_button.clicked.connect(self.primary_color_callback)
        self.primary_layout.addWidget(self.primary_button)

        # Secondary ------------------------------------------------------------
        self.secondary_widget = QWidget()
        self.secondary_layout = QHBoxLayout(self.secondary_widget)
        self.secondary_layout.setStretch(1, 1)
        self.secondary_layout.setContentsMargins(0, 0, 0, 0)
        self.secondary_layout.setSpacing(6)
        self.secondary_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.secondary_title = QLabel()
        Translations.translate_qobject(self.secondary_title, "color.secondary")
        self.secondary_layout.addWidget(self.secondary_title)
        self.secondary_button = QPushButton()
        self.secondary_button.setMinimumSize(44, 22)
        self.secondary_button.setMaximumHeight(22)
        self.edit_secondary_modal = QColorDialog()
        self.secondary_button.clicked.connect(self.secondary_color_callback)
        self.secondary_layout.addWidget(self.secondary_button)

        self.secondary_reset_button = QPushButton()
        Translations.translate_qobject(self.secondary_reset_button, "generic.reset")
        self.secondary_reset_button.clicked.connect(self.update_secondary)
        self.secondary_layout.addWidget(self.secondary_reset_button)

        # Preview Tag ----------------------------------------------------------
        self.preview_widget = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_widget)
        self.preview_layout.setStretch(1, 1)
        self.preview_layout.setContentsMargins(0, 0, 0, 6)
        self.preview_layout.setSpacing(6)
        self.preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_button = TagColorPreview(self.lib, None)
        self.preview_layout.addWidget(self.preview_button)

        # Add Widgets to Layout ================================================
        self.root_layout.addWidget(self.preview_widget)
        self.root_layout.addWidget(self.name_widget)
        self.root_layout.addWidget(self.slug_widget)
        self.root_layout.addWidget(self.primary_widget)
        self.root_layout.addWidget(self.secondary_widget)

        self.set_color(color_group or TagColorGroup("", "", Translations["color.new"], ""))
        self.update_primary(QColor(color_group.primary))
        self.update_secondary(None if not color_group.secondary else QColor(color_group.secondary))
        self.on_text_changed()

    def set_color(self, color_group: TagColorGroup):
        logger.info("[BuildColorPanel] Setting Color", color=color_group)
        self.color_group = color_group

        self.name_field.setText(color_group.name)
        self.primary_button.setText(color_group.primary)
        self.edit_primary_modal.setCurrentColor(color_group.primary)
        self.secondary_button.setText(
            Translations["color.title.no_color"]
            if not color_group.secondary
            else str(color_group.secondary)
        )
        self.edit_secondary_modal.setCurrentColor(color_group.secondary or QColor(0, 0, 0, 255))
        self.preview_button.set_tag_color_group(color_group)

    def primary_color_callback(self) -> None:
        initial = (
            self.primary_button.text()
            if self.primary_button.text().startswith("#")
            else self.color_group.primary
        )
        color = self.edit_primary_modal.getColor(initial=initial)
        if color.isValid():
            self.update_primary(color)
            self.preview_button.set_tag_color_group(self.build_color()[1])
        else:
            logger.info("[BuildColorPanel] Primary color selection was cancelled!")

    def secondary_color_callback(self) -> None:
        initial = (
            self.secondary_button.text()
            if self.secondary_button.text().startswith("#")
            else (self.color_group.secondary or QColor())
        )
        color = self.edit_secondary_modal.getColor(initial=initial)
        if color.isValid():
            self.update_secondary(color)
            self.preview_button.set_tag_color_group(self.build_color()[1])
        else:
            logger.info("[BuildColorPanel] Secondary color selection was cancelled!")

    def update_primary(self, color: QColor):
        logger.info("[BuildColorPanel] Updating Primary", primary_color=color)

        highlight_color = get_highlight_color(color)
        text_color = get_text_color(color, highlight_color)
        border_color = get_border_color(color)

        hex_code = color.name().upper()
        self.primary_button.setText(hex_code)
        self.primary_button.setStyleSheet(
            f"QPushButton{{"
            f"background: rgba{color.toTuple()};"
            f"color: rgba{text_color.toTuple()};"
            f"font-weight: 600;"
            f"border-color: rgba{border_color.toTuple()};"
            f"border-radius: 6px;"
            f"border-style:solid;"
            f"border-width: 2px;"
            f"padding-right: 4px;"
            f"padding-bottom: 1px;"
            f"padding-left: 4px;"
            f"font-size: 13px"
            f"}}"
            f"QPushButton::hover{{"
            f"border-color: rgba{highlight_color.toTuple()};"
            f"}}"
            f"QPushButton::pressed{{"
            f"background: rgba{highlight_color.toTuple()};"
            f"color: rgba{color.toTuple()};"
            f"border-color: rgba{color.toTuple()};"
            f"}}"
            f"QPushButton::focus{{"
            f"border-color: rgba{highlight_color.toTuple()};"
            f"outline:none;"
            f"}}"
        )
        self.preview_button.set_tag_color_group(self.build_color()[1])

    def update_secondary(self, color: QColor | None = None):
        logger.info("[BuildColorPanel] Updating Secondary", color=color)

        color_ = color or QColor(palette.get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT))

        highlight_color = get_highlight_color(color_)
        text_color = get_text_color(color_, highlight_color)
        border_color = get_border_color(color_)

        hex_code = "" if not color else color.name().upper()
        self.secondary_button.setText(
            Translations["color.title.no_color"] if not color else hex_code
        )
        self.secondary_button.setStyleSheet(
            f"QPushButton{{"
            f"background: rgba{color_.toTuple()};"
            f"color: rgba{text_color.toTuple()};"
            f"font-weight: 600;"
            f"border-color: rgba{border_color.toTuple()};"
            f"border-radius: 6px;"
            f"border-style:solid;"
            f"border-width: 2px;"
            f"padding-right: 4px;"
            f"padding-bottom: 1px;"
            f"padding-left: 4px;"
            f"font-size: 13px"
            f"}}"
            f"QPushButton::hover{{"
            f"border-color: rgba{highlight_color.toTuple()};"
            f"}}"
            f"QPushButton::pressed{{"
            f"background: rgba{highlight_color.toTuple()};"
            f"color: rgba{color_.toTuple()};"
            f"border-color: rgba{color_.toTuple()};"
            f"}}"
            f"QPushButton::focus{{"
            f"border-color: rgba{highlight_color.toTuple()};"
            f"outline:none;"
            f"}}"
        )
        self.preview_button.set_tag_color_group(self.build_color()[1])

    def update_preview_text(self):
        self.preview_button.button.setText(
            f"{self.name_field.text().strip() or Translations["color.placeholder"]} "
            f"({self.lib.get_namespace_name(self.color_group.namespace)})"
        )
        self.preview_button.button.setMaximumWidth(self.preview_button.button.sizeHint().width())

    def on_text_changed(self):
        try:
            self.slug_field.setText(slugify(self.name_field.text()))
        except ReservedNamespaceError:
            self.slug_field.setText(str(uuid4()))

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

        self.update_preview_text()

        if self.panel_save_button is not None:
            self.panel_save_button.setDisabled(is_name_empty)

    def build_color(self) -> tuple[TagColorGroup, TagColorGroup]:
        name = self.name_field.text()
        slug = self.slug_field.text()
        primary: str = self.primary_button.text()
        secondary: str | None = (
            self.secondary_button.text() if self.secondary_button.text().startswith("#") else None
        )

        new_color = TagColorGroup(
            slug=slug,
            namespace=self.color_group.namespace,
            name=name,
            primary=primary,
            secondary=secondary,
        )

        logger.info(
            "[BuildColorPanel] Built Color",
            slug=slug,
            namespace=self.color_group.namespace,
            name=name,
            primary=primary,
            secondary=secondary,
        )
        return (self.color_group, new_color)

    def parent_post_init(self):
        # self.setTabOrder(self.name_field, self.shorthand_field)
        # self.setTabOrder(self.shorthand_field, self.aliases_add_button)
        # self.setTabOrder(self.aliases_add_button, self.parent_tags_add_button)
        # self.setTabOrder(self.parent_tags_add_button, self.color_button)
        # self.setTabOrder(self.color_button, self.panel_cancel_button)
        # self.setTabOrder(self.panel_cancel_button, self.panel_save_button)
        # self.setTabOrder(self.panel_save_button, self.aliases_table.cellWidget(0, 1))
        self.name_field.selectAll()
        self.name_field.setFocus()
