# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from tagstudio.i18n.translations import Translations
from tagstudio.qt.app_settings import (
    MAX_CACHED_THUMB_RES,
    MIN_CACHED_THUMB_RES,
    MIN_THUMB_CACHE_SIZE,
)
from tagstudio.qt.views.styles.stylesheets import PAD


class SettingsModalView(QVBoxLayout):
    def __init__(self) -> None:
        super().__init__()
        self.setContentsMargins(0, PAD, 0, 0)

        self.library_settings_container = QWidget()
        self.appearance_settings_container = QWidget()
        self.localization_settings_container = QWidget()
        self.media_settings_container = QWidget()

        # TODO: Break into multiple tab sections for Application Settings and Library Settings
        # Tabs
        self.tab_widget = QTabWidget()

        self._build_app_settings()
        self.tab_widget.addTab(self.app_settings_container, Translations["settings.application"])

        self._build_appearance_settings()
        self.tab_widget.addTab(
            self.appearance_settings_container, Translations["settings.appearance"]
        )

        self._build_localization_settings()
        self.tab_widget.addTab(
            self.localization_settings_container, Translations["settings.localization"]
        )

        self._build_media_settings()
        self.tab_widget.addTab(self.media_settings_container, Translations["settings.media"])

        # self._build_library_settings()
        # self.tab_widget.addTab(self.library_settings_container, Translations["settings.library"])

        self.addWidget(self.tab_widget)

        # Restart Label
        self.restart_label = QLabel(Translations["settings.restart_required"])
        self.restart_label.setHidden(True)
        self.restart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.addStretch(1)
        self.addWidget(self.restart_label)

    def _build_app_settings(self):
        self.app_settings_container = QWidget()
        form_layout = QFormLayout(self.app_settings_container)
        form_layout.setContentsMargins(PAD, PAD, PAD, PAD)

        # Reopen Library on Start
        self.open_last_lib_checkbox = QCheckBox()
        form_layout.addRow(
            Translations["settings.open_library_on_start"], self.open_last_lib_checkbox
        )

        # Scan for new files when a library is opened
        self.scan_files_on_open_checkbox = QCheckBox()
        form_layout.addRow(
            Translations["settings.scan_files_on_open"], self.scan_files_on_open_checkbox
        )

        # Show Filepath
        self.filepath_combobox = QComboBox()
        form_layout.addRow(Translations["settings.filepath.label"], self.filepath_combobox)

        # Tag Click Action
        self.tag_click_action_combobox = QComboBox()
        form_layout.addRow(
            Translations["settings.tag_click_action.label"], self.tag_click_action_combobox
        )

        # Open Edit Window When Creating a Tag
        self.edit_tag_on_create_checkbox = QCheckBox()
        form_layout.addRow(
            Translations["settings.edit_tag_on_create"], self.edit_tag_on_create_checkbox
        )

        # Open Edit Window When Adding a Field
        self.edit_field_on_add_checkbox = QCheckBox()
        form_layout.addRow(
            Translations["settings.edit_field_on_add"], self.edit_field_on_add_checkbox
        )

        # Keep Tag/Field Suggest Boxes Open After Adding Items
        self.keep_suggest_boxes_open_checkbox = QCheckBox()
        form_layout.addRow(
            Translations["settings.keep_suggest_boxes_open"], self.keep_suggest_boxes_open_checkbox
        )

        # Don't Create New Items on Enter
        self.dont_create_items_on_enter_checkbox = QCheckBox()
        form_layout.addRow(
            Translations["settings.dont_create_items_on_enter"],
            self.dont_create_items_on_enter_checkbox,
        )

        # Sort Added Tags After Other Results in Suggest Box
        self.sort_added_tags_last_checkbox = QCheckBox()
        form_layout.addRow(
            Translations["settings.sort_added_tags_last"], self.sort_added_tags_last_checkbox
        )

        # Invert Suggest Box Scrolling
        self.invert_suggest_box_scroll_checkbox = QCheckBox()
        form_layout.addRow(
            Translations["settings.invert_suggest_box_scroll"],
            self.invert_suggest_box_scroll_checkbox,
        )

    # TODO: Implement Library Settings
    def _build_library_settings(self):
        form_layout = QFormLayout(self.library_settings_container)
        form_layout.setContentsMargins(PAD, PAD, PAD, PAD)

        todo_label = QLabel("TODO")
        form_layout.addRow(todo_label)

    def _build_media_settings(self):
        form_layout = QFormLayout(self.media_settings_container)
        form_layout.setContentsMargins(PAD, PAD, PAD, PAD)

        # Autoplay
        self.autoplay_checkbox = QCheckBox()
        form_layout.addRow(Translations["media_player.autoplay"], self.autoplay_checkbox)

        # Generate Thumbnails
        self.generate_thumbs = QCheckBox()
        form_layout.addRow(Translations["settings.generate_thumbs"], self.generate_thumbs)

        # Thumbnail Cache Size
        self.thumb_cache_size_container = QWidget()
        self.thumb_cache_size_layout = QHBoxLayout(self.thumb_cache_size_container)
        self.thumb_cache_size_layout.setContentsMargins(0, 0, 0, 0)
        self.thumb_cache_size_layout.setSpacing(PAD)
        self.thumb_cache_size = QLineEdit()
        self.thumb_cache_size.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.thumb_cache_size_validator = QDoubleValidator(MIN_THUMB_CACHE_SIZE, 1_000_000_000, 2)
        self.thumb_cache_size.setValidator(self.thumb_cache_size_validator)
        self.thumb_cache_size_layout.addWidget(self.thumb_cache_size)
        self.thumb_cache_size_layout.setStretch(1, 2)
        self.thumb_cache_size_layout.addWidget(QLabel("MiB"))
        form_layout.addRow(
            Translations["settings.thumb_cache_size.label"], self.thumb_cache_size_container
        )

        # Cached Thumbnail Resolution
        self.cached_thumb_res_container = QWidget()
        self.cached_thumb_res_layout = QHBoxLayout(self.cached_thumb_res_container)
        self.cached_thumb_res_layout.setContentsMargins(0, 0, 0, 0)
        self.cached_thumb_res_layout.setSpacing(PAD)
        self.cached_thumb_res = QLineEdit()
        self.cached_thumb_res.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.cached_thumb_res_validator = QIntValidator(MIN_CACHED_THUMB_RES, MAX_CACHED_THUMB_RES)
        self.cached_thumb_res.setValidator(self.cached_thumb_res_validator)
        self.cached_thumb_res_layout.addWidget(self.cached_thumb_res)
        self.cached_thumb_res_layout.setStretch(1, 2)
        self.cached_thumb_res_layout.addWidget(QLabel("px"))
        form_layout.addRow(
            Translations["settings.cached_thumb_resolution.label"], self.cached_thumb_res_container
        )

    def _build_localization_settings(self):
        form_layout = QFormLayout(self.localization_settings_container)
        form_layout.setContentsMargins(PAD, PAD, PAD, PAD)

        # Language
        self.language_combobox = QComboBox()
        form_layout.addRow(Translations["settings.language"], self.language_combobox)

        # Date Format
        self.dateformat_combobox = QComboBox()
        form_layout.addRow(Translations["settings.dateformat.label"], self.dateformat_combobox)

        # 24-Hour Format
        self.hourformat_checkbox = QCheckBox()
        form_layout.addRow(Translations["settings.hourformat.label"], self.hourformat_checkbox)

        # Zero-padding
        self.zeropadding_checkbox = QCheckBox()
        form_layout.addRow(Translations["settings.zeropadding.label"], self.zeropadding_checkbox)

    def _build_appearance_settings(self):
        form_layout = QFormLayout(self.appearance_settings_container)
        form_layout.setContentsMargins(PAD, PAD, PAD, PAD)

        # Dark Mode
        self.theme_combobox = QComboBox()
        form_layout.addRow(Translations["settings.theme.label"], self.theme_combobox)

        # Pill-Shaped Tags
        self.pill_shaped_tags_checkbox = QCheckBox()
        form_layout.addRow(
            Translations["settings.pill_shaped_tags"], self.pill_shaped_tags_checkbox
        )

        # Circular Badges
        self.circular_badges_checkbox = QCheckBox()
        form_layout.addRow(Translations["settings.circular_badges"], self.circular_badges_checkbox)
