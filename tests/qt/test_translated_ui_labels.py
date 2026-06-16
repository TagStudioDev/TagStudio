# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pytestqt.qtbot import QtBot

from tagstudio.core.enums import ShowFilepathOption, TagClickActionOption
from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.global_settings import Splash, Theme
from tagstudio.qt.mixed.settings_panel import SettingsPanel
from tagstudio.qt.mixed.tag_search import TagSearchPanel
from tagstudio.qt.translations import Translations
from tagstudio.qt.ts_qt import QtDriver
from tagstudio.qt.views.main_window import MainWindow


def _combobox_items(combobox) -> list[str]:
    return [combobox.itemText(i) for i in range(combobox.count())]


def test_option_labels_use_current_translation(qtbot: QtBot, qt_driver: QtDriver):
    original_language = Translations.current_language
    try:
        Translations.change_language("ja")
        settings_panel = SettingsPanel(qt_driver)
        qtbot.addWidget(settings_panel)

        assert _combobox_items(settings_panel.filepath_combobox) == [
            Translations["settings.filepath.option.full"],
            Translations["settings.filepath.option.relative"],
            Translations["settings.filepath.option.name"],
        ]
        assert settings_panel.filepath_combobox.itemData(0) == ShowFilepathOption.SHOW_FULL_PATHS

        assert _combobox_items(settings_panel.tag_click_action_combobox) == [
            Translations["settings.tag_click_action.open_edit"],
            Translations["settings.tag_click_action.set_search"],
            Translations["settings.tag_click_action.add_to_search"],
        ]
        assert (
            settings_panel.tag_click_action_combobox.itemData(0)
            == TagClickActionOption.OPEN_EDIT
        )

        assert _combobox_items(settings_panel.theme_combobox) == [
            Translations["settings.theme.system"],
            Translations["settings.theme.dark"],
            Translations["settings.theme.light"],
        ]
        assert settings_panel.theme_combobox.itemData(0) == Theme.SYSTEM

        assert _combobox_items(settings_panel.splash_combobox) == [
            Translations["settings.splash.option.default"],
            Translations["settings.splash.option.random"],
            Translations["settings.splash.option.classic"],
            Translations["settings.splash.option.goo_gears"],
            Translations["settings.splash.option.ninety_five"],
        ]
        assert settings_panel.splash_combobox.itemData(0) == Splash.DEFAULT
    finally:
        Translations.change_language(original_language)


def test_search_limit_all_tags_uses_current_translation(qtbot: QtBot, library: Library):
    original_language = Translations.current_language
    try:
        Translations.change_language("ja")
        tag_search_panel = TagSearchPanel(library)
        qtbot.addWidget(tag_search_panel)

        assert tag_search_panel.limit_combobox.itemText(
            tag_search_panel.limit_combobox.count() - 1
        ) == Translations["tag.all_tags"]
    finally:
        Translations.change_language(original_language)


def test_thumbnail_size_labels_use_current_translation():
    original_language = Translations.current_language
    try:
        Translations.change_language("ja")

        assert MainWindow.thumbnail_size_options() == [
            (Translations["home.thumbnail_size.extra_large"], 256),
            (Translations["home.thumbnail_size.large"], 192),
            (Translations["home.thumbnail_size.medium"], 128),
            (Translations["home.thumbnail_size.small"], 96),
            (Translations["home.thumbnail_size.mini"], 76),
        ]
    finally:
        Translations.change_language(original_language)
