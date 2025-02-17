# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFormLayout, QLabel, QVBoxLayout, QWidget
from src.core.enums import SettingItems
from src.qt.translations import Translations
from src.qt.widgets.panel import PanelWidget


class SettingsPanel(PanelWidget):
    def __init__(self, driver):
        super().__init__()
        self.driver = driver
        self.setMinimumSize(320, 200)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 0, 6, 0)

        self.form_container = QWidget()
        self.form_layout = QFormLayout(self.form_container)
        self.form_layout.setContentsMargins(0, 0, 0, 0)

        self.restart_label = QLabel()
        self.restart_label.setHidden(True)
        Translations.translate_qobject(self.restart_label, "settings.restart_required")
        self.restart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        language_label = QLabel()
        Translations.translate_qobject(language_label, "settings.language")
        languages = [
            # "cs", # Minimal
            # "da", # Minimal
            "de",
            "en",
            "es",
            "fil",
            "fr",
            "hu",
            # "it", # Minimal
            "nb_NO",
            "pl",
            "pt_BR",
            # "pt", # Empty
            "ru",
            "sv",
            "ta",
            "tok",
            "tr",
            # "yue_Hant", # Empty
            "zh_Hant",
        ]
        self.language_combobox = QComboBox()
        self.language_combobox.addItems(languages)
        current_lang: str = str(
            driver.settings.value(SettingItems.LANGUAGE, defaultValue="en", type=str)
        )
        current_lang = "en" if current_lang not in languages else current_lang
        self.language_combobox.setCurrentIndex(languages.index(current_lang))
        self.language_combobox.currentIndexChanged.connect(
            lambda: self.restart_label.setHidden(False)
        )
        self.form_layout.addRow(language_label, self.language_combobox)

        self.root_layout.addWidget(self.form_container)
        self.root_layout.addStretch(1)
        self.root_layout.addWidget(self.restart_label)

    def get_language(self) -> str:
        return self.language_combobox.currentText()
