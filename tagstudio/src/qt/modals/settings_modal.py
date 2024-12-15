import copy

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
        self.tempSettings = copy.deepcopy(settings)

        self.main = QVBoxLayout(self)

        # ---
        self.darkMode_Label = QLabel()
        self.darkMode_Value = QCheckBox()
        self.darkMode_Row = QHBoxLayout()
        self.darkMode_Row.addWidget(self.darkMode_Label)
        self.darkMode_Row.addWidget(self.darkMode_Value)

        self.darkMode_Label.setText("Dark Mode")
        self.darkMode_Value.setChecked(self.tempSettings.dark_mode)

        self.darkMode_Value.stateChanged.connect(
            lambda state: self.set_property("dark_mode", bool(state))
        )

        # ---
        self.language_Label = QLabel()
        self.language_Value = QComboBox()
        self.language_Row = QHBoxLayout()
        self.language_Row.addWidget(self.language_Label)
        self.language_Row.addWidget(self.language_Value)

        self.language_Label.setText("Language")
        language_list = [  # TODO: put this somewhere else
            "en-US",
            "en-GB",
            "es-MX",
            # etc...
        ]
        self.language_Value.addItems(language_list)
        self.language_Value.setCurrentIndex(language_list.index(self.tempSettings.language))
        self.language_Value.currentTextChanged.connect(
            lambda text: self.set_property("language", text)
        )

        # ---
        self.main.addLayout(self.darkMode_Row)
        self.main.addLayout(self.language_Row)

    def set_property(self, prop_name: str, value: any) -> None:
        setattr(self.tempSettings, prop_name, value)

    def get_content(self) -> TSSettings:
        return self.tempSettings
