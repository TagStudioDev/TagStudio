# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.translations import Translations

# Only import for type checking/autocompletion, will not be imported at runtime.
if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver


class LibraryInfoWindowView(QWidget):
    def __init__(self, library: "Library", driver: "QtDriver"):
        super().__init__()
        self.lib = library
        self.driver = driver

        self.setWindowTitle("Library Information")
        self.setMinimumSize(400, 300)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 6, 6, 6)

        row_height: int = 22
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
        self.body_layout.setSpacing(0)

        # Statistics -----------------------------------------------------------
        self.stats_widget = QWidget()
        self.stats_layout = QVBoxLayout(self.stats_widget)
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

        self.entries_row: int = 0
        self.tags_row: int = 1
        self.fields_row: int = 2
        self.namespaces_row: int = 3
        self.colors_row: int = 4
        self.macros_row: int = 5

        self.labels_col: int = 0
        self.values_col: int = 2
        self.buttons_col: int = 4

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

        self.stats_grid_layout.addWidget(self.entries_label, self.entries_row, self.labels_col)
        self.stats_grid_layout.addWidget(self.tags_label, self.tags_row, self.labels_col)
        self.stats_grid_layout.addWidget(self.fields_label, self.fields_row, self.labels_col)
        self.stats_grid_layout.addWidget(
            self.namespaces_label, self.namespaces_row, self.labels_col
        )
        self.stats_grid_layout.addWidget(self.colors_label, self.colors_row, self.labels_col)
        self.stats_grid_layout.addWidget(self.macros_label, self.macros_row, self.labels_col)

        self.stats_grid_layout.setRowMinimumHeight(self.entries_row, row_height)
        self.stats_grid_layout.setRowMinimumHeight(self.tags_row, row_height)
        self.stats_grid_layout.setRowMinimumHeight(self.fields_row, row_height)
        self.stats_grid_layout.setRowMinimumHeight(self.namespaces_row, row_height)
        self.stats_grid_layout.setRowMinimumHeight(self.colors_row, row_height)
        self.stats_grid_layout.setRowMinimumHeight(self.macros_row, row_height)

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

        self.stats_grid_layout.addWidget(self.entry_count_label, self.entries_row, self.values_col)
        self.stats_grid_layout.addWidget(self.tag_count_label, self.tags_row, self.values_col)
        self.stats_grid_layout.addWidget(self.field_count_label, self.fields_row, self.values_col)
        self.stats_grid_layout.addWidget(
            self.namespaces_count_label, self.namespaces_row, self.values_col
        )
        self.stats_grid_layout.addWidget(self.color_count_label, self.colors_row, self.values_col)
        self.stats_grid_layout.addWidget(self.macros_count_label, self.macros_row, self.values_col)

        self.manage_tags_button = QPushButton(Translations["edit.tag_manager"])
        self.manage_colors_button = QPushButton(Translations["color_manager.title"])

        self.stats_grid_layout.addWidget(self.manage_tags_button, self.tags_row, self.buttons_col)
        self.stats_grid_layout.addWidget(
            self.manage_colors_button, self.colors_row, self.buttons_col
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

        # Buttons
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
        self.root_layout.addWidget(self.button_container)
