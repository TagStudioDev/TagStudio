import copy
from pathlib import Path
from typing import Any

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)
from src.core.settings import TSSettings
from src.qt.translations import Translations
from src.qt.widgets.panel import PanelWidget


class SettingsModal(PanelWidget):
    def __init__(self, settings: TSSettings):
        super().__init__()
        self.tempSettings: TSSettings = copy.deepcopy(settings)

        self.main = QVBoxLayout(self)

        # ---
        language_row = QHBoxLayout(self)
        language_label = QLabel(self)
        Translations.translate_qobject(language_label, "settings.language")
        language_value = QComboBox(self)
        language_row.addWidget(language_label)
        language_row.addWidget(language_value)

        translations_folder = Path("tagstudio/resources/translations")
        language_list = [x.stem for x in translations_folder.glob("*.json")]
        language_value.addItems(language_list)
        language_value.setCurrentIndex(language_list.index(self.tempSettings.language))
        language_value.currentTextChanged.connect(
            lambda text: setattr(self.tempSettings, "language", text)
        )

        # ---
        show_filenames_row = QHBoxLayout(self)
        show_filenames_label = QLabel(self)
        Translations.translate_qobject(show_filenames_label, "settings.show_filenames_in_grid")
        show_filenames_value = QCheckBox(self)

        show_filenames_value.setChecked(self.tempSettings.show_filenames_in_grid)
        show_filenames_row.addWidget(show_filenames_label)
        show_filenames_row.addWidget(show_filenames_value)

        show_filenames_value.stateChanged.connect(
            lambda state: setattr(self.tempSettings, "show_filenames_in_grid", bool(state))
        )
        # ---

        self.main.addLayout(language_row)
        self.main.addLayout(show_filenames_row)

    def set_property(self, prop_name: str, value: Any) -> None:
        setattr(self.tempSettings, prop_name, value)

    def get_content(self):
        return self.tempSettings
