# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import TYPE_CHECKING, Any, override

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QDialogButtonBox, QLineEdit

from tagstudio.core.library.library_settings import (
    DEFAULT_CACHED_THUMB_RES,
    DEFAULT_THUMB_CACHE_SIZE,
    MAX_CACHED_THUMB_RES,
    MIN_CACHED_THUMB_RES,
    MIN_THUMB_CACHE_SIZE,
)
from tagstudio.i18n.translations import DEFAULT_TRANSLATION, LANGUAGES, Translations
from tagstudio.qt.app_settings import ShowFilepathOption, TagClickActionOption, ThemeOption
from tagstudio.qt.controllers.capsule import Capsule
from tagstudio.qt.controllers.modal import Modal
from tagstudio.qt.controllers.modal_content import ModalContent
from tagstudio.qt.controllers.tag_capsule_box import TagCapsuleBox
from tagstudio.qt.controllers.tag_search_panel import TagSearchPanel
from tagstudio.qt.views.settings_modal_view import SettingsModalView
from tagstudio.qt.views.styles.stylesheets import TagShape

if TYPE_CHECKING:
    from tagstudio.qt.qt_driver import QtDriver


class SettingsModal(ModalContent):
    edited = Signal()

    filepath_option_map: dict[ShowFilepathOption, str] = {
        ShowFilepathOption.SHOW_FULL_PATHS: "settings.filepath.option.full",
        ShowFilepathOption.SHOW_RELATIVE_PATHS: "settings.filepath.option.relative",
        ShowFilepathOption.SHOW_FILENAMES_ONLY: "settings.filepath.option.name",
    }

    theme_map: dict[ThemeOption, str] = {
        ThemeOption.SYSTEM: "settings.theme.system",
        ThemeOption.DARK: "settings.theme.dark",
        ThemeOption.LIGHT: "settings.theme.light",
    }

    tag_click_action_map: dict[TagClickActionOption, str] = {
        TagClickActionOption.OPEN_EDIT: "settings.tag_click_action.open_edit",
        TagClickActionOption.SET_SEARCH: "settings.tag_click_action.set_search",
        TagClickActionOption.ADD_TO_SEARCH: "settings.tag_click_action.add_to_search",
    }

    date_format_map: dict[str, str] = {
        "%d/%m/%y": "21/08/24",
        "%d/%m/%Y": "21/08/2024",
        "%d.%m.%y": "21.08.24",
        "%d.%m.%Y": "21.08.2024",
        "%d-%m-%y": "21-08-24",
        "%d-%m-%Y": "21-08-2024",
        "%x": "08/21/24",
        "%m/%d/%Y": "08/21/2024",
        "%m-%d-%y": "08-21-24",
        "%m-%d-%Y": "08-21-2024",
        "%m.%d.%y": "08.21.24",
        "%m.%d.%Y": "08.21.2024",
        "%Y/%m/%d": "2024/08/21",
        "%Y-%m-%d": "2024-08-21",
        "%Y.%m.%d": "2024.08.21",
    }

    def __init__(self, driver: QtDriver):
        super().__init__()
        self._driver = driver
        self.setMinimumSize(400, 500)
        self.setLayout(SettingsModalView())
        view = self.layout()

        view.open_last_lib_checkbox.setChecked(driver.app_settings.open_last_loaded_on_startup)

        for k in SettingsModal.filepath_option_map:
            view.filepath_combobox.addItem(Translations[SettingsModal.filepath_option_map[k]], k)
        view.filepath_combobox.setCurrentIndex(
            list(SettingsModal.filepath_option_map.keys()).index(driver.app_settings.show_filepath)
        )

        for k in SettingsModal.tag_click_action_map:
            view.tag_click_action_combobox.addItem(
                Translations[SettingsModal.tag_click_action_map[k]], k
            )
        view.tag_click_action_combobox.setCurrentIndex(
            list(SettingsModal.tag_click_action_map.keys()).index(
                driver.app_settings.tag_click_action
            )
        )

        view.edit_tag_on_create_checkbox.setChecked(driver.app_settings.edit_tag_on_create)
        view.edit_field_on_add_checkbox.setChecked(driver.app_settings.edit_field_on_add)
        view.keep_suggest_boxes_open_checkbox.setChecked(
            driver.app_settings.keep_suggest_boxes_open
        )
        view.dont_create_items_on_enter_checkbox.setChecked(
            driver.app_settings.dont_create_items_on_enter
        )
        view.sort_added_tags_last_checkbox.setChecked(driver.app_settings.sort_added_tags_last)
        view.invert_suggest_box_scroll_checkbox.setChecked(
            driver.app_settings.invert_suggest_box_scroll
        )
        view.autoplay_checkbox.setChecked(driver.app_settings.autoplay)

        for k in SettingsModal.theme_map:
            view.theme_combobox.addItem(Translations[SettingsModal.theme_map[k]], k)
        view.theme_combobox.setCurrentIndex(
            list(SettingsModal.theme_map.keys()).index(driver.app_settings.theme)
        )

        view.pill_shaped_tags_checkbox.setChecked(driver.app_settings.pill_shaped_tags)
        view.circular_badges_checkbox.setChecked(driver.app_settings.circular_badges)

        translated_langs = [(Translations[f"language.{lang}"], lang) for lang in LANGUAGES]
        translated_langs.sort(key=lambda x: x[0])

        for lang in translated_langs:
            view.language_combobox.addItem(lang[0], lang[1])
        current_lang: str = driver.app_settings.language
        if current_lang not in LANGUAGES:
            current_lang = DEFAULT_TRANSLATION
        view.language_combobox.setCurrentIndex([x[1] for x in translated_langs].index(current_lang))
        view.language_combobox.currentIndexChanged.connect(self._update_restart_label)

        for k in SettingsModal.date_format_map:
            view.dateformat_combobox.addItem(SettingsModal.date_format_map[k], k)
        dateformat: str = driver.app_settings.date_format
        if dateformat not in SettingsModal.date_format_map:
            dateformat = "%x"
        view.dateformat_combobox.setCurrentIndex(
            list(SettingsModal.date_format_map.keys()).index(dateformat)
        )

        view.hourformat_checkbox.setChecked(driver.app_settings.hour_format)
        view.zeropadding_checkbox.setChecked(driver.app_settings.zero_padding)

        view.sync_on_open_checkbox.setChecked(driver.lib.settings.sync_on_open)
        view.generate_thumbs.setChecked(driver.lib.settings.generate_thumbs)
        view.thumb_cache_size.setText(
            str(max(driver.lib.settings.thumb_cache_size, MIN_THUMB_CACHE_SIZE)).removesuffix(".0")
        )
        view.cached_thumb_res.setText(str(driver.lib.settings.cached_thumb_resolution))
        view.tab_widget.setTabEnabled(
            view.tab_widget.indexOf(view.library_settings_container),
            driver.lib.library_dir is not None,
        )

        for checkbox in self.findChildren(QCheckBox):
            checkbox.toggled.connect(self.edited)
        for combobox in self.findChildren(QComboBox):
            combobox.currentIndexChanged.connect(self.edited)
        for line_edit in self.findChildren(QLineEdit):
            line_edit.textChanged.connect(self.edited)

        self._update_restart_label()

    def _update_restart_label(self):
        view = self.layout()
        show_label = view.language_combobox.currentData() != Translations.current_language
        view.restart_label.setHidden(not show_label)

    def get_app_settings(self) -> dict[str, Any]:
        view = self.layout()
        return {
            "language": view.language_combobox.currentData(),
            "open_last_loaded_on_startup": view.open_last_lib_checkbox.isChecked(),
            "autoplay": view.autoplay_checkbox.isChecked(),
            "show_filepath": view.filepath_combobox.currentData(),
            "theme": view.theme_combobox.currentData(),
            "pill_shaped_tags": view.pill_shaped_tags_checkbox.isChecked(),
            "circular_badges": view.circular_badges_checkbox.isChecked(),
            "tag_click_action": view.tag_click_action_combobox.currentData(),
            "edit_tag_on_create": view.edit_tag_on_create_checkbox.isChecked(),
            "edit_field_on_add": view.edit_field_on_add_checkbox.isChecked(),
            "keep_suggest_boxes_open": view.keep_suggest_boxes_open_checkbox.isChecked(),
            "dont_create_items_on_enter": view.dont_create_items_on_enter_checkbox.isChecked(),
            "sort_added_tags_last": view.sort_added_tags_last_checkbox.isChecked(),
            "invert_suggest_box_scroll": view.invert_suggest_box_scroll_checkbox.isChecked(),
            "date_format": view.dateformat_combobox.currentData(),
            "hour_format": view.hourformat_checkbox.isChecked(),
            "zero_padding": view.zeropadding_checkbox.isChecked(),
        }

    def get_library_settings(self) -> dict[str, Any]:
        view = self.layout()
        thumb_cache_size, is_size_number = view.thumb_cache_size_validator.locale().toDouble(
            view.thumb_cache_size.text() or str(DEFAULT_THUMB_CACHE_SIZE)
        )
        if not is_size_number:
            thumb_cache_size = self._driver.lib.settings.thumb_cache_size
        cached_thumb_res, is_res_number = view.cached_thumb_res_validator.locale().toInt(
            view.cached_thumb_res.text() or str(DEFAULT_CACHED_THUMB_RES)
        )
        if not is_res_number:
            cached_thumb_res = self._driver.lib.settings.cached_thumb_resolution
        return {
            "sync_on_open": view.sync_on_open_checkbox.isChecked(),
            "generate_thumbs": view.generate_thumbs.isChecked(),
            "thumb_cache_size": max(thumb_cache_size, MIN_THUMB_CACHE_SIZE),
            "cached_thumb_resolution": min(
                max(cached_thumb_res, MIN_CACHED_THUMB_RES), MAX_CACHED_THUMB_RES
            ),
        }

    def has_pending_changes(self) -> bool:
        """Whether any setting here differs from the saved ones."""
        app_settings = self.get_app_settings()
        library_settings = self.get_library_settings()
        return any(
            value != getattr(self._driver.app_settings, key) for key, value in app_settings.items()
        ) or any(
            value != getattr(self._driver.lib.settings, key)
            for key, value in library_settings.items()
        )

    def update_settings(self):
        driver = self._driver
        app_settings = self.get_app_settings()

        driver.app_settings.language = app_settings["language"]
        driver.app_settings.open_last_loaded_on_startup = app_settings[
            "open_last_loaded_on_startup"
        ]
        driver.app_settings.autoplay = app_settings["autoplay"]
        driver.app_settings.show_filepath = app_settings["show_filepath"]
        driver.app_settings.theme = app_settings["theme"]
        driver.app_settings.pill_shaped_tags = app_settings["pill_shaped_tags"]
        driver.app_settings.circular_badges = app_settings["circular_badges"]
        driver.app_settings.tag_click_action = app_settings["tag_click_action"]
        driver.app_settings.edit_tag_on_create = app_settings["edit_tag_on_create"]
        driver.app_settings.edit_field_on_add = app_settings["edit_field_on_add"]
        driver.app_settings.keep_suggest_boxes_open = app_settings["keep_suggest_boxes_open"]
        driver.app_settings.dont_create_items_on_enter = app_settings["dont_create_items_on_enter"]
        driver.app_settings.sort_added_tags_last = app_settings["sort_added_tags_last"]
        driver.app_settings.invert_suggest_box_scroll = app_settings["invert_suggest_box_scroll"]
        driver.app_settings.date_format = app_settings["date_format"]
        driver.app_settings.hour_format = app_settings["hour_format"]
        driver.app_settings.zero_padding = app_settings["zero_padding"]

        driver.app_settings.save()

        lib = driver.lib
        if lib.library_dir is not None:
            library_settings = self.get_library_settings()
            lib.settings.sync_on_open = library_settings["sync_on_open"]
            lib.settings.generate_thumbs = library_settings["generate_thumbs"]
            lib.settings.thumb_cache_size = library_settings["thumb_cache_size"]
            lib.settings.cached_thumb_resolution = library_settings["cached_thumb_resolution"]
            lib.settings.save()

        # Apply changes
        if driver.applied_theme != app_settings["theme"]:
            driver.apply_theme()
        TagShape.is_pill = app_settings["pill_shaped_tags"]
        TagShape.is_circle_badge = app_settings["circular_badges"]
        # Restyle displayed tags and containers so they take the new shape and padding
        for widget in QApplication.allWidgets():
            if isinstance(widget, (Capsule, TagCapsuleBox, TagSearchPanel)):
                widget.restyle()
        # Update main_window to refresh badge shape
        driver.main_window.update()
        # Show File Path
        driver.update_recent_lib_menu()
        driver.main_window.inspector.update_from_selection()
        library_directory = driver.lib.library_dir
        if app_settings["show_filepath"] == ShowFilepathOption.SHOW_FULL_PATHS:
            display_path = library_directory or ""
        else:
            display_path = library_directory.name if library_directory else ""
        driver.main_window.setWindowTitle(
            Translations.format("app.title", base_title=driver.base_title, library_dir=display_path)
        )

    @classmethod
    def build_modal(cls, driver: QtDriver, show_library_settings: bool = False) -> Modal:
        settings_modal = cls(driver)
        if show_library_settings:
            view = settings_modal.layout()
            view.tab_widget.setCurrentWidget(view.library_settings_container)

        modal = Modal(
            content_widget=settings_modal,
            window_title=Translations["settings.title"],
            is_savable=True,
        )
        modal.saved.connect(settings_modal.update_settings)
        apply_button = modal.layout().button_box.addButton(
            Translations["generic.apply"], QDialogButtonBox.ButtonRole.ApplyRole
        )

        def update_apply_button() -> None:
            apply_button.setEnabled(settings_modal.has_pending_changes())

        apply_button.clicked.connect(settings_modal.update_settings)
        apply_button.clicked.connect(update_apply_button)
        settings_modal.edited.connect(update_apply_button)
        update_apply_button()
        modal.layout().title_label.setVisible(False)

        return modal

    @override
    def layout(self) -> SettingsModalView:
        layout = super().layout()
        assert isinstance(layout, SettingsModalView)
        return layout
