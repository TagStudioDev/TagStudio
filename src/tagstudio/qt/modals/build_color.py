# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import contextlib

import structlog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QFormLayout,
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
from src.core.library.alchemy.library import slugify
from src.core.library.alchemy.models import TagColorGroup
from src.core.palette import ColorType, UiColor, get_tag_color, get_ui_color
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
        self.color_group: TagColorGroup = color_group
        self.tag_color_namespace: str | None
        self.tag_color_slug: str | None
        self.disambiguation_id: int | None

        self.known_colors: set[str]
        self.update_known_colors()

        self.setMinimumSize(340, 240)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 0, 6, 0)
        self.root_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.form_container = QWidget()
        self.form_layout = QFormLayout(self.form_container)
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)

        # Preview Tag ----------------------------------------------------------
        self.preview_widget = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_widget)
        self.preview_layout.setStretch(1, 1)
        self.preview_layout.setContentsMargins(0, 0, 0, 6)
        self.preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_button = TagColorPreview(self.lib, None)
        self.preview_button.setEnabled(False)
        self.preview_layout.addWidget(self.preview_button)

        # Name -----------------------------------------------------------------
        self.name_title = QLabel(Translations["library_object.name"])
        self.name_field = QLineEdit()
        self.name_field.setFixedHeight(24)
        self.name_field.textChanged.connect(self.on_text_changed)
        self.name_field.setPlaceholderText(Translations["library_object.name_required"])
        self.form_layout.addRow(self.name_title, self.name_field)

        # Slug -----------------------------------------------------------------
        self.slug_title = QLabel(Translations["library_object.slug"])
        self.slug_field = QLineEdit()
        self.slug_field.setEnabled(False)
        self.slug_field.setFixedHeight(24)
        self.slug_field.setPlaceholderText(Translations["library_object.slug_required"])
        self.form_layout.addRow(self.slug_title, self.slug_field)

        # Primary --------------------------------------------------------------
        self.primary_title = QLabel(Translations["color.primary"])
        self.primary_button = QPushButton()
        self.primary_button.setMinimumSize(44, 22)
        self.primary_button.setMaximumHeight(22)
        self.edit_primary_modal = QColorDialog()
        self.primary_button.clicked.connect(self.primary_color_callback)
        self.form_layout.addRow(self.primary_title, self.primary_button)

        # Secondary ------------------------------------------------------------
        self.secondary_widget = QWidget()
        self.secondary_layout = QHBoxLayout(self.secondary_widget)
        self.secondary_layout.setContentsMargins(0, 0, 0, 0)
        self.secondary_layout.setSpacing(6)
        self.secondary_title = QLabel(Translations["color.secondary"])
        self.secondary_button = QPushButton()
        self.secondary_button.setMinimumSize(44, 22)
        self.secondary_button.setMaximumHeight(22)
        self.edit_secondary_modal = QColorDialog()
        self.secondary_button.clicked.connect(self.secondary_color_callback)
        self.secondary_layout.addWidget(self.secondary_button)

        self.secondary_reset_button = QPushButton(Translations["generic.reset"])
        self.secondary_reset_button.clicked.connect(self.update_secondary)
        self.secondary_layout.addWidget(self.secondary_reset_button)
        self.secondary_layout.setStretch(0, 3)
        self.secondary_layout.setStretch(1, 1)
        self.form_layout.addRow(self.secondary_title, self.secondary_widget)

        # Color Border ---------------------------------------------------------
        self.border_widget = QWidget()
        self.border_layout = QHBoxLayout(self.border_widget)
        self.border_layout.setStretch(1, 1)
        self.border_layout.setContentsMargins(0, 0, 0, 0)
        self.border_layout.setSpacing(6)
        self.border_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.border_checkbox = QCheckBox()
        self.border_checkbox.setFixedSize(22, 22)
        self.border_checkbox.clicked.connect(
            lambda checked: self.update_secondary(
                color=QColor(self.preview_button.tag_color_group.secondary)
                if self.preview_button.tag_color_group.secondary
                else None,
                color_border=checked,
            )
        )
        self.border_layout.addWidget(self.border_checkbox)
        self.border_label = QLabel(Translations["color.color_border"])
        self.border_layout.addWidget(self.border_label)

        primary_color = QColor(get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT))
        border_color = get_border_color(primary_color)
        highlight_color = get_highlight_color(primary_color)
        text_color: QColor = get_text_color(primary_color, highlight_color)
        self.border_checkbox.setStyleSheet(
            f"QCheckBox{{"
            f"background: rgba{primary_color.toTuple()};"
            f"color: rgba{text_color.toTuple()};"
            f"border-color: rgba{border_color.toTuple()};"
            f"border-radius: 6px;"
            f"border-style:solid;"
            f"border-width: 2px;"
            f"}}"
            f"QCheckBox::indicator{{"
            f"width: 10px;"
            f"height: 10px;"
            f"border-radius: 2px;"
            f"margin: 4px;"
            f"}}"
            f"QCheckBox::indicator:checked{{"
            f"background: rgba{text_color.toTuple()};"
            f"}}"
            f"QCheckBox::hover{{"
            f"border-color: rgba{highlight_color.toTuple()};"
            f"}}"
            f"QCheckBox::focus{{"
            f"border-color: rgba{highlight_color.toTuple()};"
            f"outline:none;"
            f"}}"
        )

        # Add Widgets to Layout ================================================
        self.root_layout.addWidget(self.preview_widget)
        self.root_layout.addWidget(self.form_container)
        self.root_layout.addWidget(self.border_widget)

        self.set_color(color_group or TagColorGroup("", "", Translations["color.new"], ""))
        self.update_primary(QColor(color_group.primary))
        self.update_secondary(None if not color_group.secondary else QColor(color_group.secondary))
        self.on_text_changed()

    def set_color(self, color_group: TagColorGroup):
        logger.info("[BuildColorPanel] Setting Color", color=color_group)
        self.color_group = color_group

        self.preview_button.set_tag_color_group(color_group)
        self.name_field.setText(color_group.name)
        self.primary_button.setText(color_group.primary)
        self.edit_primary_modal.setCurrentColor(color_group.primary)
        self.secondary_button.setText(
            Translations["color.title.no_color"]
            if not color_group.secondary
            else str(color_group.secondary)
        )
        self.edit_secondary_modal.setCurrentColor(color_group.secondary or QColor(0, 0, 0, 255))
        self.border_checkbox.setChecked(color_group.color_border)

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
            f"padding-right: 0px;"
            f"padding-left: 0px;"
            f"outline-style: solid;"
            f"outline-width: 1px;"
            f"outline-radius: 4px;"
            f"outline-color: rgba{text_color.toTuple()};"
            f"}}"
        )
        self.preview_button.set_tag_color_group(self.build_color()[1])

    def update_secondary(self, color: QColor | None = None, color_border: bool = False):
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
            f"padding-right: 0px;"
            f"padding-left: 0px;"
            f"outline-style: solid;"
            f"outline-width: 1px;"
            f"outline-radius: 4px;"
            f"outline-color: rgba{text_color.toTuple()};"
            f"}}"
        )
        self.preview_button.set_tag_color_group(self.build_color()[1])

    def update_known_colors(self):
        groups = self.lib.tag_color_groups
        colors = groups.get(self.color_group.namespace, [])
        self.known_colors = {c.slug for c in colors}
        with contextlib.suppress(KeyError):
            self.known_colors.remove(self.color_group.slug)

    def update_preview_text(self):
        self.preview_button.button.setText(
            f"{self.name_field.text().strip() or Translations["color.placeholder"]} "
            f"({self.lib.get_namespace_name(self.color_group.namespace)})"
        )
        self.preview_button.button.setMaximumWidth(self.preview_button.button.sizeHint().width())

    def no_collide(self, slug: str) -> str:
        """Return a slug name that's verified not to collide with other known color slugs."""
        if slug and slug in self.known_colors:
            split_slug: list[str] = slug.rsplit("-", 1)
            suffix: str = ""
            if len(split_slug) > 1:
                suffix = split_slug[1]

            if suffix:
                try:
                    suffix_num: int = int(suffix)
                    return self.no_collide(f"{split_slug[0]}-{suffix_num+1}")
                except ValueError:
                    return self.no_collide(f"{slug}-2")
            else:
                return self.no_collide(f"{slug}-2")
        return slug

    def on_text_changed(self):
        slug = self.no_collide(slugify(self.name_field.text().strip(), allow_reserved=True))

        is_name_empty = not self.name_field.text().strip()
        is_slug_empty = not slug
        is_invalid = False

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

        self.slug_field.setText(slug)
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
        color_border: bool = self.border_checkbox.isChecked()

        new_color = TagColorGroup(
            slug=slug,
            namespace=self.color_group.namespace,
            name=name,
            primary=primary,
            secondary=secondary,
            color_border=color_border,
        )

        logger.info(
            "[BuildColorPanel] Built Color",
            slug=new_color.slug,
            namespace=new_color.namespace,
            name=new_color.name,
            primary=new_color.primary,
            secondary=new_color.secondary,
            color_border=new_color.color_border,
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
