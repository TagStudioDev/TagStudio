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
from src.qt.widgets.panel import PanelWidget


class SettingsModal(PanelWidget):
    def __init__(self, settings: TSSettings):
        super().__init__()
        self.tempSettings: TSSettings = copy.deepcopy(settings)

        self.main = QVBoxLayout(self)

        # ---
        self.language_Label = QLabel()
        self.language_Value = QComboBox()
        self.language_Row = QHBoxLayout()
        self.language_Row.addWidget(self.language_Label)
        self.language_Row.addWidget(self.language_Value)

        self.language_Label.setText("Language")
        translations_folder = Path("tagstudio/resources/translations")
        language_list = [x.stem for x in translations_folder.glob("*.json")]
        self.language_Value.addItems(language_list)
        self.language_Value.setCurrentIndex(language_list.index(self.tempSettings.language))
        self.language_Value.currentTextChanged.connect(
            lambda text: setattr(self.tempSettings, "language", text)
        )

        # ---
        self.show_library_list_Label = QLabel()
        self.show_library_list_Value = QCheckBox()
        self.show_library_list_Row = QHBoxLayout()
        self.show_library_list_Row.addWidget(self.show_library_list_Label)
        self.show_library_list_Row.addWidget(self.show_library_list_Value)
        self.show_library_list_Label.setText("Load library list on startup (requires restart):")
        self.show_library_list_Value.setChecked(self.tempSettings.show_library_list)

        self.show_library_list_Value.stateChanged.connect(
            lambda state: setattr(self.tempSettings, "show_library_list", bool(state))
        )

        # ---
        self.show_filenames_Label = QLabel()
        self.show_filenames_Value = QCheckBox()
        self.show_filenames_Row = QHBoxLayout()
        self.show_filenames_Row.addWidget(self.show_filenames_Label)
        self.show_filenames_Row.addWidget(self.show_filenames_Value)
        self.show_filenames_Label.setText("Show filenames in grid (requires restart)")
        self.show_filenames_Value.setChecked(self.tempSettings.show_filenames_in_grid)

        self.show_filenames_Value.stateChanged.connect(
            lambda state: setattr(self.tempSettings, "show_filenames_in_grid", bool(state))
        )
        # ---
        self.main.addLayout(self.language_Row)
        self.main.addLayout(self.show_library_list_Row)
        self.main.addLayout(self.show_filenames_Row)

    def set_property(self, prop_name: str, value: Any) -> None:
        setattr(self.tempSettings, prop_name, value)

    def get_content(self):
        return self.tempSettings
