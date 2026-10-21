# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import typing

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSpacerItem,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from tagstudio.core.library.alchemy.enums import SortingModeEnum
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.browsing_area import BrowsingArea
from tagstudio.qt.controllers.inspector import Inspector
from tagstudio.qt.controllers.search_bar import SearchBar
from tagstudio.qt.views.styles.stylesheets import HALF_PAD, PAD, WIN_PAD, checkbox_style

if typing.TYPE_CHECKING:
    from tagstudio.qt.qt_driver import QtDriver


class MainWindowView(QHBoxLayout):
    THUMB_SIZES: list[tuple[str, int]] = [
        ("home.thumbnail_size.extra_large", 256),
        ("home.thumbnail_size.large", 192),
        ("home.thumbnail_size.medium", 128),
        ("home.thumbnail_size.small", 96),
        ("home.thumbnail_size.mini", 76),
    ]

    extra_input_layout: QHBoxLayout
    results_label: QLabel
    show_hidden_entries_widget: QWidget
    show_hidden_entries_layout: QHBoxLayout
    show_hidden_entries_title: QLabel
    show_hidden_entries_checkbox: QCheckBox
    sorting_mode_combobox: QComboBox
    sorting_direction_combobox: QComboBox
    thumb_size_combobox: QComboBox

    def __init__(self, driver: QtDriver, pixel_ratio: float) -> None:
        super().__init__()
        self.setContentsMargins(0, WIN_PAD, 0, 0)

        self.search_bar = SearchBar(driver.lib)
        self.setup_extra_input_bar()
        self.browsing_area = BrowsingArea(driver, pixel_ratio)
        self.inspector = Inspector(driver)

        central_content = QWidget()
        central_content.setObjectName("central_content")
        central_content_layout = QVBoxLayout(central_content)
        central_content_layout.setContentsMargins(0, 0, 0, 0)
        central_content_layout.setSpacing(PAD)
        central_content_layout.addWidget(self.search_bar)
        central_content_layout.addLayout(self.extra_input_layout)
        central_content_layout.addWidget(self.browsing_area)

        self.content_splitter = QSplitter()
        self.content_splitter.setObjectName("content_splitter")
        self.content_splitter.setHandleWidth(PAD + HALF_PAD)
        self.content_splitter.addWidget(central_content)
        self.content_splitter.addWidget(self.inspector)
        self.content_splitter.setStretchFactor(0, 1)
        self.addWidget(self.content_splitter)

    def setup_extra_input_bar(self):
        """Sets up inputs for sorting settings and thumbnail size."""
        self.extra_input_layout = QHBoxLayout()
        self.extra_input_layout.setObjectName("extra_input_layout")
        self.extra_input_layout.setContentsMargins(WIN_PAD, 0, 0, 0)

        self.results_label = QLabel("")
        self.results_label.setObjectName("results_label")
        self.extra_input_layout.addWidget(self.results_label)
        self.extra_input_layout.addItem(
            QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        # Show hidden entries checkbox
        self.show_hidden_entries_widget = QWidget()
        self.show_hidden_entries_layout = QHBoxLayout(self.show_hidden_entries_widget)
        self.show_hidden_entries_layout.setStretch(1, 1)
        self.show_hidden_entries_layout.setContentsMargins(0, 0, 0, 0)
        self.show_hidden_entries_layout.setSpacing(PAD)
        self.show_hidden_entries_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.show_hidden_entries_title = QLabel(Translations["home.show_hidden_entries"])
        self.show_hidden_entries_checkbox = QCheckBox()
        self.show_hidden_entries_checkbox.setFixedSize(22, 22)
        self.show_hidden_entries_checkbox.setStyleSheet(checkbox_style())
        self.show_hidden_entries_checkbox.setChecked(False)  # Default: No

        self.show_hidden_entries_layout.addWidget(self.show_hidden_entries_checkbox)
        self.show_hidden_entries_layout.addWidget(self.show_hidden_entries_title)
        self.extra_input_layout.addWidget(self.show_hidden_entries_widget)

        # Sorting Mode Dropdown
        self.sorting_mode_combobox = QComboBox()
        self.sorting_mode_combobox.setObjectName("sorting_mode_combobox")
        for sort_mode in SortingModeEnum:
            self.sorting_mode_combobox.addItem(Translations[sort_mode.value], sort_mode)
        self.extra_input_layout.addWidget(self.sorting_mode_combobox)

        # Sorting Direction Dropdown
        self.sorting_direction_combobox = QComboBox()
        self.sorting_direction_combobox.setObjectName("sorting_direction_combobox")
        self.sorting_direction_combobox.addItem(
            Translations["sorting.direction.ascending"], userData=True
        )
        self.sorting_direction_combobox.addItem(
            Translations["sorting.direction.descending"], userData=False
        )
        self.sorting_direction_combobox.setCurrentIndex(1)  # Default: Descending
        self.extra_input_layout.addWidget(self.sorting_direction_combobox)

        # Thumbnail Size placeholder
        self.thumb_size_combobox = QComboBox()
        self.thumb_size_combobox.setObjectName("thumb_size_combobox")
        self.thumb_size_combobox.setPlaceholderText(Translations["home.thumbnail_size"])
        self.thumb_size_combobox.setCurrentText("")
        size_policy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.thumb_size_combobox.sizePolicy().hasHeightForWidth())
        self.thumb_size_combobox.setSizePolicy(size_policy)
        self.thumb_size_combobox.setMinimumWidth(128)
        self.thumb_size_combobox.setMaximumWidth(352)
        self.extra_input_layout.addWidget(self.thumb_size_combobox)
        for size in MainWindowView.THUMB_SIZES:
            self.thumb_size_combobox.addItem(Translations[size[0]], size[1])
        self.thumb_size_combobox.setCurrentIndex(2)  # Default: Medium
