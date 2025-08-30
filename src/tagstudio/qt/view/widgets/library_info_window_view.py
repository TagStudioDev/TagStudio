# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import math
from typing import TYPE_CHECKING

from PIL import Image, ImageQt
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from tagstudio.qt.helpers.color_overlay import theme_fg_overlay
from tagstudio.qt.translations import Translations

# Only import for type checking/autocompletion, will not be imported at runtime.
if TYPE_CHECKING:
    from tagstudio.core.library.alchemy.library import Library
    from tagstudio.qt.ts_qt import QtDriver


class LibraryInfoWindowView(QWidget):
    def __init__(self, library: "Library", driver: "QtDriver"):
        super().__init__()
        self.lib = library
        self.driver = driver

        self.setWindowTitle("Library Information")
        self.setMinimumSize(800, 480)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 6, 6, 6)

        row_height: int = 22
        icon_margin: int = 4
        cell_alignment: Qt.AlignmentFlag = (
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        # Title ----------------------------------------------------------------
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Body (Stats, etc.) ---------------------------------------------------
        self.body_widget = QWidget()
        self.body_layout = QHBoxLayout(self.body_widget)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(6)

        # Statistics -----------------------------------------------------------
        self.stats_widget = QWidget()
        self.stats_layout = QVBoxLayout(self.stats_widget)
        self.stats_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.stats_layout.setContentsMargins(0, 0, 0, 0)
        self.stats_layout.setSpacing(12)

        self.stats_label = QLabel(f"<h3>{Translations['library_info.stats']}</h3>")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.stats_grid: QWidget = QWidget()
        self.stats_grid_layout: QGridLayout = QGridLayout(self.stats_grid)
        self.stats_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.stats_grid_layout.setSpacing(0)
        self.stats_grid_layout.setColumnMinimumWidth(1, 12)
        self.stats_grid_layout.setColumnMinimumWidth(3, 12)

        self.stats_entries_row: int = 0
        self.stats_tags_row: int = 1
        self.stats_fields_row: int = 2
        self.stats_namespaces_row: int = 3
        self.stats_colors_row: int = 4
        self.stats_macros_row: int = 5

        # NOTE: Alternating rows for visual padding
        self.stats_labels_col: int = 0
        self.stats_values_col: int = 2
        self.stats_buttons_col: int = 4

        self.entries_label: QLabel = QLabel(Translations["library_info.stats.entries"])
        self.entries_label.setAlignment(cell_alignment)
        self.tags_label: QLabel = QLabel(Translations["library_info.stats.tags"])
        self.tags_label.setAlignment(cell_alignment)
        self.fields_label: QLabel = QLabel(Translations["library_info.stats.fields"])
        self.fields_label.setAlignment(cell_alignment)
        self.namespaces_label: QLabel = QLabel(Translations["library_info.stats.namespaces"])
        self.namespaces_label.setAlignment(cell_alignment)
        self.colors_label: QLabel = QLabel(Translations["library_info.stats.colors"])
        self.colors_label.setAlignment(cell_alignment)
        self.macros_label: QLabel = QLabel(Translations["library_info.stats.macros"])
        self.macros_label.setAlignment(cell_alignment)

        self.stats_grid_layout.addWidget(
            self.entries_label,
            self.stats_entries_row,
            self.stats_labels_col,
        )
        self.stats_grid_layout.addWidget(
            self.tags_label,
            self.stats_tags_row,
            self.stats_labels_col,
        )
        self.stats_grid_layout.addWidget(
            self.fields_label,
            self.stats_fields_row,
            self.stats_labels_col,
        )
        self.stats_grid_layout.addWidget(
            self.namespaces_label,
            self.stats_namespaces_row,
            self.stats_labels_col,
        )
        self.stats_grid_layout.addWidget(
            self.colors_label,
            self.stats_colors_row,
            self.stats_labels_col,
        )
        self.stats_grid_layout.addWidget(
            self.macros_label,
            self.stats_macros_row,
            self.stats_labels_col,
        )

        self.stats_grid_layout.setRowMinimumHeight(self.stats_entries_row, row_height)
        self.stats_grid_layout.setRowMinimumHeight(self.stats_tags_row, row_height)
        self.stats_grid_layout.setRowMinimumHeight(self.stats_fields_row, row_height)
        self.stats_grid_layout.setRowMinimumHeight(self.stats_namespaces_row, row_height)
        self.stats_grid_layout.setRowMinimumHeight(self.stats_colors_row, row_height)
        self.stats_grid_layout.setRowMinimumHeight(self.stats_macros_row, row_height)

        self.entry_count_label: QLabel = QLabel()
        self.entry_count_label.setAlignment(cell_alignment)
        self.tag_count_label: QLabel = QLabel()
        self.tag_count_label.setAlignment(cell_alignment)
        self.field_count_label: QLabel = QLabel()
        self.field_count_label.setAlignment(cell_alignment)
        self.namespaces_count_label: QLabel = QLabel()
        self.namespaces_count_label.setAlignment(cell_alignment)
        self.color_count_label: QLabel = QLabel()
        self.color_count_label.setAlignment(cell_alignment)
        self.macros_count_label: QLabel = QLabel()
        self.macros_count_label.setAlignment(cell_alignment)

        self.stats_grid_layout.addWidget(
            self.entry_count_label,
            self.stats_entries_row,
            self.stats_values_col,
        )
        self.stats_grid_layout.addWidget(
            self.tag_count_label,
            self.stats_tags_row,
            self.stats_values_col,
        )
        self.stats_grid_layout.addWidget(
            self.field_count_label,
            self.stats_fields_row,
            self.stats_values_col,
        )
        self.stats_grid_layout.addWidget(
            self.namespaces_count_label,
            self.stats_namespaces_row,
            self.stats_values_col,
        )
        self.stats_grid_layout.addWidget(
            self.color_count_label,
            self.stats_colors_row,
            self.stats_values_col,
        )
        self.stats_grid_layout.addWidget(
            self.macros_count_label,
            self.stats_macros_row,
            self.stats_values_col,
        )

        self.manage_tags_button = QPushButton(Translations["edit.tag_manager"])
        self.manage_colors_button = QPushButton(Translations["color_manager.title"])

        self.stats_grid_layout.addWidget(
            self.manage_tags_button,
            self.stats_tags_row,
            self.stats_buttons_col,
        )
        self.stats_grid_layout.addWidget(
            self.manage_colors_button,
            self.stats_colors_row,
            self.stats_buttons_col,
        )

        self.stats_layout.addWidget(self.stats_label)
        self.stats_layout.addWidget(self.stats_grid)

        self.body_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )
        self.body_layout.addWidget(self.stats_widget)
        self.body_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        # Vertical Separator
        self.vertical_sep = QFrame()
        self.vertical_sep.setFrameShape(QFrame.Shape.VLine)
        self.vertical_sep.setFrameShadow(QFrame.Shadow.Plain)
        opacity_effect_vert_sep = QGraphicsOpacityEffect(self)
        opacity_effect_vert_sep.setOpacity(0.1)
        self.vertical_sep.setGraphicsEffect(opacity_effect_vert_sep)
        self.body_layout.addWidget(self.vertical_sep)

        # Cleanup --------------------------------------------------------------
        self.cleanup_widget = QWidget()
        self.cleanup_layout = QVBoxLayout(self.cleanup_widget)
        self.cleanup_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.cleanup_layout.setContentsMargins(0, 0, 0, 0)
        self.cleanup_layout.setSpacing(12)

        self.cleanup_label = QLabel(f"<h3>{Translations['library_info.cleanup']}</h3>")
        self.cleanup_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.cleanup_grid: QWidget = QWidget()
        self.cleanup_grid_layout: QGridLayout = QGridLayout(self.cleanup_grid)
        self.cleanup_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.cleanup_grid_layout.setSpacing(0)
        self.cleanup_grid_layout.setColumnMinimumWidth(1, 12)
        self.cleanup_grid_layout.setColumnMinimumWidth(3, 6)
        self.cleanup_grid_layout.setColumnMinimumWidth(5, 6)

        self.cleanup_layout.addWidget(self.cleanup_label)
        self.cleanup_layout.addWidget(self.cleanup_grid)

        self.cleanup_unlinked_row: int = 0
        self.cleanup_ignored_row: int = 1
        self.cleanup_dupe_files_row: int = 2
        self.cleanup_section_break_row: int = 3
        self.cleanup_legacy_json_row: int = 4
        self.cleanup_backups_row: int = 5

        # NOTE: Alternating rows for visual padding
        self.cleanup_labels_col: int = 0
        self.cleanup_values_col: int = 2
        self.cleanup_icons_col: int = 4
        self.cleanup_buttons_col: int = 6

        # Horizontal Separator
        self.horizontal_sep = QFrame()
        self.horizontal_sep.setFrameShape(QFrame.Shape.HLine)
        self.horizontal_sep.setFrameShadow(QFrame.Shadow.Plain)
        self.horizontal_sep.setFixedHeight(row_height)
        opacity_effect_hor_sep = QGraphicsOpacityEffect(self)
        opacity_effect_hor_sep.setOpacity(0.1)
        self.horizontal_sep.setGraphicsEffect(opacity_effect_hor_sep)
        self.cleanup_grid_layout.addWidget(
            self.horizontal_sep,
            self.cleanup_section_break_row,
            self.cleanup_labels_col,
            1,
            7,
            Qt.AlignmentFlag.AlignVCenter,
        )

        self.unlinked_icon = QLabel()
        unlinked_image: Image.Image = self.driver.rm.get("unlinked_stat")  # pyright: ignore[reportAssignmentType]
        unlinked_pixmap = QPixmap.fromImage(ImageQt.ImageQt(unlinked_image))
        unlinked_pixmap.setDevicePixelRatio(self.devicePixelRatio())
        unlinked_pixmap = unlinked_pixmap.scaledToWidth(
            math.floor((row_height - icon_margin) * self.devicePixelRatio()),
            Qt.TransformationMode.SmoothTransformation,
        )
        self.unlinked_icon.setPixmap(unlinked_pixmap)

        self.ignored_icon = QLabel()
        ignored_image: Image.Image = self.driver.rm.get("ignored_stat")  # pyright: ignore[reportAssignmentType]
        ignored_pixmap = QPixmap.fromImage(ImageQt.ImageQt(ignored_image))
        ignored_pixmap.setDevicePixelRatio(self.devicePixelRatio())
        ignored_pixmap = ignored_pixmap.scaledToWidth(
            math.floor((row_height - icon_margin) * self.devicePixelRatio()),
            Qt.TransformationMode.SmoothTransformation,
        )
        self.ignored_icon.setPixmap(ignored_pixmap)

        self.dupe_file_icon = QLabel()
        dupe_file_image: Image.Image = self.driver.rm.get("dupe_file_stat")  # pyright: ignore[reportAssignmentType]
        dupe_file_pixmap = QPixmap.fromImage(
            ImageQt.ImageQt(theme_fg_overlay(dupe_file_image, use_alpha=False))
        )
        dupe_file_pixmap.setDevicePixelRatio(self.devicePixelRatio())
        dupe_file_pixmap = dupe_file_pixmap.scaledToWidth(
            math.floor((row_height - icon_margin) * self.devicePixelRatio()),
            Qt.TransformationMode.SmoothTransformation,
        )
        self.dupe_file_icon.setPixmap(dupe_file_pixmap)

        self.cleanup_grid_layout.addWidget(
            self.unlinked_icon,
            self.cleanup_unlinked_row,
            self.cleanup_icons_col,
        )
        self.cleanup_grid_layout.addWidget(
            self.ignored_icon,
            self.cleanup_ignored_row,
            self.cleanup_icons_col,
        )
        self.cleanup_grid_layout.addWidget(
            self.dupe_file_icon,
            self.cleanup_dupe_files_row,
            self.cleanup_icons_col,
        )

        self.unlinked_label: QLabel = QLabel(Translations["library_info.cleanup.unlinked"])
        self.unlinked_label.setAlignment(cell_alignment)
        self.ignored_label: QLabel = QLabel(Translations["library_info.cleanup.ignored"])
        self.ignored_label.setAlignment(cell_alignment)
        self.dupe_files_label: QLabel = QLabel(Translations["library_info.cleanup.dupe_files"])
        self.dupe_files_label.setAlignment(cell_alignment)
        self.legacy_json_label: QLabel = QLabel(Translations["library_info.cleanup.legacy_json"])
        self.legacy_json_label.setAlignment(cell_alignment)
        self.backups_label: QLabel = QLabel(Translations["library_info.cleanup.backups"])
        self.backups_label.setAlignment(cell_alignment)

        self.cleanup_grid_layout.addWidget(
            self.unlinked_label,
            self.cleanup_unlinked_row,
            self.cleanup_labels_col,
        )
        self.cleanup_grid_layout.addWidget(
            self.ignored_label,
            self.cleanup_ignored_row,
            self.cleanup_labels_col,
        )
        self.cleanup_grid_layout.addWidget(
            self.dupe_files_label,
            self.cleanup_dupe_files_row,
            self.cleanup_labels_col,
        )
        self.cleanup_grid_layout.addWidget(
            self.legacy_json_label,
            self.cleanup_legacy_json_row,
            self.cleanup_labels_col,
        )
        self.cleanup_grid_layout.addWidget(
            self.backups_label,
            self.cleanup_backups_row,
            self.cleanup_labels_col,
        )

        self.cleanup_grid_layout.setRowMinimumHeight(self.cleanup_unlinked_row, row_height)
        self.cleanup_grid_layout.setRowMinimumHeight(self.cleanup_ignored_row, row_height)
        self.cleanup_grid_layout.setRowMinimumHeight(self.cleanup_dupe_files_row, row_height)
        self.cleanup_grid_layout.setRowMinimumHeight(self.cleanup_legacy_json_row, row_height)
        self.cleanup_grid_layout.setRowMinimumHeight(self.cleanup_backups_row, row_height)

        self.unlinked_count_label: QLabel = QLabel()
        self.unlinked_count_label.setAlignment(cell_alignment)
        self.ignored_count_label: QLabel = QLabel()
        self.ignored_count_label.setAlignment(cell_alignment)
        self.dupe_files_count_label: QLabel = QLabel()
        self.dupe_files_count_label.setAlignment(cell_alignment)
        self.legacy_json_status_label: QLabel = QLabel()
        self.legacy_json_status_label.setAlignment(cell_alignment)
        self.backups_count_label: QLabel = QLabel()
        self.backups_count_label.setAlignment(cell_alignment)

        self.cleanup_grid_layout.addWidget(
            self.unlinked_count_label,
            self.cleanup_unlinked_row,
            self.cleanup_values_col,
        )
        self.cleanup_grid_layout.addWidget(
            self.ignored_count_label,
            self.cleanup_ignored_row,
            self.cleanup_values_col,
        )
        self.cleanup_grid_layout.addWidget(
            self.dupe_files_count_label,
            self.cleanup_dupe_files_row,
            self.cleanup_values_col,
        )
        self.cleanup_grid_layout.addWidget(
            self.legacy_json_status_label,
            self.cleanup_legacy_json_row,
            self.cleanup_values_col,
        )
        self.cleanup_grid_layout.addWidget(
            self.backups_count_label,
            self.cleanup_backups_row,
            self.cleanup_values_col,
        )

        self.fix_unlinked_entries = QPushButton(Translations["menu.tools.fix_unlinked_entries"])
        self.fix_ignored_entries = QPushButton(Translations["menu.tools.fix_ignored_entries"])
        self.fix_dupe_files = QPushButton(Translations["menu.tools.fix_duplicate_files"])

        self.cleanup_grid_layout.addWidget(
            self.fix_unlinked_entries,
            self.cleanup_unlinked_row,
            self.cleanup_buttons_col,
        )
        self.cleanup_grid_layout.addWidget(
            self.fix_ignored_entries,
            self.cleanup_ignored_row,
            self.cleanup_buttons_col,
        )
        self.cleanup_grid_layout.addWidget(
            self.fix_dupe_files,
            self.cleanup_dupe_files_row,
            self.cleanup_buttons_col,
        )

        self.body_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )
        self.body_layout.addWidget(self.cleanup_widget)
        self.body_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        # Details --------------------------------------------------------------
        self.details_container = QWidget()
        self.details_layout = QHBoxLayout(self.details_container)
        self.details_layout.setContentsMargins(6, 0, 6, 0)
        opacity_effect_details = QGraphicsOpacityEffect(self)
        opacity_effect_details.setOpacity(0.5)

        self.version_label = QLabel()
        self.version_label.setGraphicsEffect(opacity_effect_details)
        self.details_layout.addWidget(self.version_label)

        # Buttons --------------------------------------------------------------
        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(6, 6, 6, 6)
        self.button_layout.addStretch(1)

        self.close_button = QPushButton(Translations["generic.close"])
        self.button_layout.addWidget(self.close_button)

        # Add to root layout ---------------------------------------------------
        self.root_layout.addWidget(self.title_label)
        self.root_layout.addWidget(self.body_widget)
        self.root_layout.addStretch(1)
        self.root_layout.addStretch(2)
        self.root_layout.addWidget(self.details_container)
        self.root_layout.addWidget(self.button_container)
