# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFormLayout, QLabel, QVBoxLayout, QWidget

from tagstudio.core.enums import SettingItems, ShowFilepathOption
from tagstudio.qt.translations import Translations
from tagstudio.qt.widgets.panel import PanelWidget


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

        self.restart_label = QLabel(Translations["settings.restart_required"])
        self.restart_label.setHidden(True)
        self.restart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        language_label = QLabel(Translations["settings.language"])
        self.languages = {
            # "Cantonese (Traditional)": "yue_Hant",  # Empty
            "Chinese (Traditional)": "zh_Hant",
            # "Czech": "cs",  # Minimal
            # "Danish": "da",  # Minimal
            "Dutch": "nl",
            "English": "en",
            "Filipino": "fil",
            "French": "fr",
            "German": "de",
            "Hungarian": "hu",
            # "Italian": "it",  # Minimal
            "Norwegian Bokmål": "nb_NO",
            "Polish": "pl",
            "Portuguese (Brazil)": "pt_BR",
            # "Portuguese (Portugal)": "pt",  # Empty
            "Russian": "ru",
            "Spanish": "es",
            "Swedish": "sv",
            "Tamil": "ta",
            "Toki Pona": "tok",
            "Turkish": "tr",
        }
        self.language_combobox = QComboBox()
        self.language_combobox.addItems(list(self.languages.keys()))
        current_lang: str = str(
            driver.settings.value(SettingItems.LANGUAGE, defaultValue="en", type=str)
        )
        current_lang = "en" if current_lang not in self.languages.values() else current_lang
        self.language_combobox.setCurrentIndex(list(self.languages.values()).index(current_lang))
        self.language_combobox.currentIndexChanged.connect(
            lambda: self.restart_label.setHidden(False)
        )
        self.form_layout.addRow(language_label, self.language_combobox)

        filepath_option_map: dict[int, str] = {
            ShowFilepathOption.SHOW_FULL_PATHS: Translations["settings.filepath.option.full"],
            ShowFilepathOption.SHOW_RELATIVE_PATHS: Translations[
                "settings.filepath.option.relative"
            ],
            ShowFilepathOption.SHOW_FILENAMES_ONLY: Translations["settings.filepath.option.name"],
        }
        self.filepath_combobox = QComboBox()
        self.filepath_combobox.addItems(list(filepath_option_map.values()))
        filepath_option: int = int(
            driver.settings.value(
                SettingItems.SHOW_FILEPATH, defaultValue=ShowFilepathOption.DEFAULT.value, type=int
            )
        )
        filepath_option = 0 if filepath_option not in filepath_option_map else filepath_option
        self.filepath_combobox.setCurrentIndex(filepath_option)
        self.filepath_combobox.currentIndexChanged.connect(self.apply_filepath_setting)
        self.form_layout.addRow(Translations["settings.filepath.label"], self.filepath_combobox)

        self.root_layout.addWidget(self.form_container)
        self.root_layout.addStretch(1)
        self.root_layout.addWidget(self.restart_label)

    def get_language(self) -> str:
        values: list[str] = list(self.languages.values())
        return values[self.language_combobox.currentIndex()]

    def apply_filepath_setting(self):
        selected_value = self.filepath_combobox.currentIndex()
        self.driver.settings.setValue(SettingItems.SHOW_FILEPATH, selected_value)
        self.driver.update_recent_lib_menu()
        self.driver.preview_panel.update_widgets()
        library_directory = self.driver.lib.library_dir
        if selected_value == ShowFilepathOption.SHOW_FULL_PATHS:
            display_path = library_directory
        else:
            display_path = library_directory.name
        self.driver.main_window.setWindowTitle(
            Translations.format(
                "app.title", base_title=self.driver.base_title, library_dir=display_path
            )
        )
