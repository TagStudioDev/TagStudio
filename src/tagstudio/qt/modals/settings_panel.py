# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from tagstudio.core.driver import DriverMixin
from tagstudio.core.enums import SettingItems
from tagstudio.qt.translations import LANGUAGES, Translations
from tagstudio.qt.widgets.panel import PanelModal, PanelWidget


class SettingsPanel(PanelWidget):
    def __init__(self, driver):
        super().__init__()
        self.driver = driver
        self.setMinimumSize(320, 200)

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 6, 0, 0)

        # Tabs
        self.tab_widget = QTabWidget()

        self.__build_global_settings(driver)
        self.tab_widget.addTab(self.global_settings_container, Translations["settings.global"])

        self.__build_library_settings(driver)
        self.tab_widget.addTab(self.library_settings_container, Translations["settings.library"])

        self.root_layout.addWidget(self.tab_widget)

        # Restart Label
        self.restart_label = QLabel(Translations["settings.restart_required"])
        self.restart_label.setHidden(True)
        self.restart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.root_layout.addStretch(1)
        self.root_layout.addWidget(self.restart_label)

    def __build_global_settings(self, driver):
        self.global_settings_container = QWidget()
        form_layout = QFormLayout(self.global_settings_container)
        form_layout.setContentsMargins(6, 6, 6, 6)

        language_label = QLabel(Translations["settings.language"])
        self.language_combobox = QComboBox()
        self.language_combobox.addItems(list(LANGUAGES.keys()))
        current_lang: str = str(
            driver.settings.value(SettingItems.LANGUAGE, defaultValue="en", type=str)
        )
        current_lang = "en" if current_lang not in LANGUAGES.values() else current_lang
        self.language_combobox.setCurrentIndex(list(LANGUAGES.values()).index(current_lang))
        self.language_combobox.currentIndexChanged.connect(
            lambda: self.restart_label.setHidden(False)
        )
        form_layout.addRow(language_label, self.language_combobox)

    def __build_library_settings(self, driver):
        self.library_settings_container = QWidget()
        form_layout = QFormLayout(self.global_settings_container)
        form_layout.setContentsMargins(6, 6, 6, 6)

    def get_language(self) -> str:
        values: list[str] = list(LANGUAGES.values())
        return values[self.language_combobox.currentIndex()]

    @classmethod
    def build_modal(cls, driver: DriverMixin) -> PanelModal:
        settings_panel = cls(driver)

        def update_language():
            Translations.change_language(settings_panel.get_language())
            driver.settings.setValue(SettingItems.LANGUAGE, settings_panel.get_language())
            driver.settings.sync()

        modal = PanelModal(
            widget=settings_panel,
            done_callback=update_language,
            has_save=False,
        )
        modal.title_widget.setVisible(False)
        modal.setWindowTitle(Translations["settings.title"])

        return modal
