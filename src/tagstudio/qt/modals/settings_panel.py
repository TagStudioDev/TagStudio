# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from typing import TYPE_CHECKING

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

from tagstudio.core.enums import ShowFilepathOption
from tagstudio.qt.translations import LANGUAGES, Translations
from tagstudio.qt.widgets.panel import PanelModal, PanelWidget

if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

FILEPATH_OPTION_MAP: dict[ShowFilepathOption, str] = {
    ShowFilepathOption.SHOW_FULL_PATHS: Translations["settings.filepath.option.full"],
    ShowFilepathOption.SHOW_RELATIVE_PATHS: Translations["settings.filepath.option.relative"],
    ShowFilepathOption.SHOW_FILENAMES_ONLY: Translations["settings.filepath.option.name"],
}


class SettingsPanel(PanelWidget):
    driver: "QtDriver"

    def __init__(self, driver: "QtDriver"):
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

    def __build_global_settings(self, driver: "QtDriver"):
        self.global_settings_container = QWidget()
        form_layout = QFormLayout(self.global_settings_container)
        form_layout.setContentsMargins(6, 6, 6, 6)

        # Language
        self.language_combobox = QComboBox()
        self.language_combobox.addItems(list(LANGUAGES.keys()))
        current_lang: str = driver.settings.language
        if current_lang not in LANGUAGES.values():
            current_lang = "en"
        self.language_combobox.setCurrentIndex(list(LANGUAGES.values()).index(current_lang))
        self.language_combobox.currentIndexChanged.connect(
            lambda: self.restart_label.setHidden(False)
        )
        form_layout.addRow(Translations["settings.language"], self.language_combobox)

        # Open Last Library on Start
        self.open_last_lib_checkbox = QCheckBox()
        self.open_last_lib_checkbox.setChecked(driver.settings.open_last_loaded_on_startup)
        form_layout.addRow(
            Translations["settings.open_library_on_start"], self.open_last_lib_checkbox
        )

        # Autoplay
        self.autoplay_checkbox = QCheckBox()
        self.autoplay_checkbox.setChecked(driver.settings.autoplay)
        form_layout.addRow(Translations["media_player.autoplay"], self.autoplay_checkbox)

        # Show Filenames in Grid
        self.show_filenames_checkbox = QCheckBox()
        self.show_filenames_checkbox.setChecked(driver.settings.show_filenames_in_grid)
        form_layout.addRow(
            Translations["settings.show_filenames_in_grid"], self.show_filenames_checkbox
        )

        # Page Size
        self.page_size_line_edit = QLineEdit()
        self.page_size_line_edit.setText(str(driver.settings.page_size))

        def on_page_size_changed():
            text = self.page_size_line_edit.text()
            if not text.isdigit() or int(text) < 1:
                self.page_size_line_edit.setText(str(driver.settings.page_size))

        self.page_size_line_edit.editingFinished.connect(on_page_size_changed)
        form_layout.addRow(Translations["settings.page_size"], self.page_size_line_edit)

        # Show Filepath
        self.filepath_combobox = QComboBox()
        for k in FILEPATH_OPTION_MAP:
            self.filepath_combobox.addItem(FILEPATH_OPTION_MAP[k], k)
        filepath_option: ShowFilepathOption = driver.settings.show_filepath
        if filepath_option not in FILEPATH_OPTION_MAP:
            filepath_option = ShowFilepathOption.DEFAULT
        self.filepath_combobox.setCurrentIndex(
            list(FILEPATH_OPTION_MAP.keys()).index(filepath_option)
        )
        form_layout.addRow(Translations["settings.filepath.label"], self.filepath_combobox)

        # Dark Mode
        self.dark_mode_checkbox = QCheckBox()
        self.dark_mode_checkbox.setChecked(driver.settings.dark_mode)
        self.dark_mode_checkbox.checkStateChanged.connect(
            lambda: self.restart_label.setHidden(
                self.dark_mode_checkbox.isChecked() == driver.settings.dark_mode
            )
        )
        form_layout.addRow(Translations["settings.dark_mode"], self.dark_mode_checkbox)

    def __build_library_settings(self, driver: "QtDriver"):
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
            "show_filepath": self.filepath_combobox.currentData(),
            "dark_mode": self.dark_mode_checkbox.isChecked(),
        }

    def update_settings(self, driver: "QtDriver"):
        settings = self.get_settings()

        driver.settings.language = settings["language"]
        driver.settings.open_last_loaded_on_startup = settings["open_last_loaded_on_startup"]
        driver.settings.autoplay = settings["autoplay"]
        driver.settings.show_filenames_in_grid = settings["show_filenames_in_grid"]
        driver.settings.page_size = settings["page_size"]
        driver.settings.show_filepath = settings["show_filepath"]
        driver.settings.dark_mode = settings["dark_mode"]

        driver.settings.save()

        # Apply changes
        # Language
        Translations.change_language(settings["language"])

        # Show File Path
        driver.update_recent_lib_menu()
        driver.preview_panel.update_widgets()
        library_directory = driver.lib.library_dir
        if settings["show_filepath"] == ShowFilepathOption.SHOW_FULL_PATHS:
            display_path = library_directory or ""
        else:
            display_path = library_directory.name if library_directory else ""
        driver.main_window.setWindowTitle(
            Translations.format("app.title", base_title=driver.base_title, library_dir=display_path)
        )

    @classmethod
    def build_modal(cls, driver: "QtDriver") -> PanelModal:
        settings_panel = cls(driver)

        modal = PanelModal(
            widget=settings_panel,
            done_callback=lambda: settings_panel.update_settings(driver),
            has_save=False,
        )
        modal.title_widget.setVisible(False)
        modal.setWindowTitle(Translations["settings.title"])

        return modal
