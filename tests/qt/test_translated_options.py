# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT

# pyright: reportPrivateUsage=false

from collections.abc import Iterator

import pytest
from PySide6.QtWidgets import QComboBox
from pytestqt.qtbot import QtBot

from tagstudio.i18n.translations import DEFAULT_TRANSLATION, Translations
from tagstudio.qt.controllers.edit_field_template_modal import EditFieldTemplateModal
from tagstudio.qt.mixed.settings_panel import SettingsPanel
from tagstudio.qt.qt_driver import QtDriver


@pytest.fixture
def french() -> Iterator[None]:
    # Like the app, switch language only after these modules have been imported.
    Translations.change_language("fr")
    yield
    Translations.change_language(DEFAULT_TRANSLATION)


def items(combobox: QComboBox) -> list[str]:
    return [combobox.itemText(i) for i in range(combobox.count())]


def test_settings_options_use_the_current_language(qtbot: QtBot, qt_driver: QtDriver, french: None):
    # qt_driver applies the language from its settings, so request french after it.
    panel = SettingsPanel(qt_driver)
    qtbot.addWidget(panel)

    assert "Sombre" in items(panel.theme_combobox)
    assert "Aléatoire" in items(panel.splash_combobox)
    assert "Afficher le Chemin Complet" in items(panel.filepath_combobox)
    assert "Modifier le Tag" in items(panel.tag_click_action_combobox)


@pytest.mark.usefixtures("french")
def test_field_type_options_use_the_current_language(qtbot: QtBot):
    modal = EditFieldTemplateModal()
    qtbot.addWidget(modal)

    assert "Texte" in items(modal._type_combobox)
