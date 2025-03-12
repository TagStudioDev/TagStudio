# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from tagstudio.core.driver import DriverMixin
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

        # Language
        language_label = QLabel(Translations["settings.language"])
        self.language_combobox = QComboBox()
        self.language_combobox.addItems(list(LANGUAGES.keys()))
        current_lang: str = driver.settings.language
        if current_lang not in LANGUAGES.values():
            current_lang = "en"
        self.language_combobox.setCurrentIndex(list(LANGUAGES.values()).index(current_lang))
        self.language_combobox.currentIndexChanged.connect(
            lambda: self.restart_label.setHidden(False)
        )
        form_layout.addRow(language_label, self.language_combobox)

        # Open Last Library on Start
        open_last_lib_label = QLabel(Translations["settings.open_library_on_start"])
        self.open_last_lib_checkbox = QCheckBox()
        self.open_last_lib_checkbox.setChecked(driver.settings.open_last_loaded_on_startup)
        form_layout.addRow(open_last_lib_label, self.open_last_lib_checkbox)

        # Autoplay
        autoplay_label = QLabel(Translations["media_player.autoplay"])
        self.autoplay_checkbox = QCheckBox()
        self.autoplay_checkbox.setChecked(driver.settings.autoplay)
        form_layout.addRow(autoplay_label, self.autoplay_checkbox)

        # Show Filenames in Grid
        show_filenames_label = QLabel(Translations["settings.show_filenames_in_grid"])
        self.show_filenames_checkbox = QCheckBox()
        self.show_filenames_checkbox.setChecked(driver.settings.show_filenames_in_grid)
        form_layout.addRow(show_filenames_label, self.show_filenames_checkbox)

        # Page Size
        page_size_label = QLabel(Translations["settings.page_size"])
        self.page_size_line_edit = QLineEdit()
        self.page_size_line_edit.setText(str(driver.settings.page_size))

        def on_page_size_changed():
            text = self.page_size_line_edit.text()
            if not text.isdigit() or int(text) < 1:
                self.page_size_line_edit.setText(str(driver.settings.page_size))

        self.page_size_line_edit.editingFinished.connect(on_page_size_changed)
        form_layout.addRow(page_size_label, self.page_size_line_edit)

    def __build_library_settings(self, driver):
        self.library_settings_container = QWidget()
        form_layout = QFormLayout(self.library_settings_container)
        form_layout.setContentsMargins(6, 6, 6, 6)

        todo_label = QLabel("TODO")
        form_layout.addRow(todo_label)

    def get_settings(self) -> dict:
        return {
            "language": list(LANGUAGES.values())[self.language_combobox.currentIndex()],
            "open_last_loaded_on_startup": self.open_last_lib_checkbox.isChecked(),
            "autoplay": self.autoplay_checkbox.isChecked(),
            "show_filenames_in_grid": self.show_filenames_checkbox.isChecked(),
            "page_size": int(self.page_size_line_edit.text()),
        }

    @classmethod
    def build_modal(cls, driver: DriverMixin) -> PanelModal:
        settings_panel = cls(driver)

        def update_settings():
            settings = settings_panel.get_settings()

            Translations.change_language(settings["language"])
            driver.settings.language = settings["language"]

            driver.settings.open_last_loaded_on_startup = settings["open_last_loaded_on_startup"]
            driver.settings.autoplay = settings["autoplay"]
            driver.settings.show_filenames_in_grid = settings["show_filenames_in_grid"]
            driver.settings.page_size = settings["page_size"]

            driver.settings.save()

        modal = PanelModal(
            widget=settings_panel,
            done_callback=update_settings,
            has_save=False,
        )
        modal.title_widget.setVisible(False)
        modal.setWindowTitle(Translations["settings.title"])

        return modal
