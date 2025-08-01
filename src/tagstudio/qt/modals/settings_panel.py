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

from tagstudio.core.enums import ShowFilepathOption, TagClickActionOption
from tagstudio.core.global_settings import Theme
from tagstudio.qt.translations import DEFAULT_TRANSLATION, LANGUAGES, Translations
from tagstudio.qt.widgets.panel import PanelModal, PanelWidget

if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

FILEPATH_OPTION_MAP: dict[ShowFilepathOption, str] = {}

THEME_MAP: dict[Theme, str] = {}

TAG_CLICK_ACTION_MAP: dict[TagClickActionOption, str] = {}

DATE_FORMAT_MAP: dict[str, str] = {
    "%d/%m/%y": "21/08/24",
    "%d/%m/%Y": "21/08/2024",
    "%d.%m.%y": "21.08.24",
    "%d.%m.%Y": "21.08.2024",
    "%d-%m-%y": "21-08-24",
    "%d-%m-%Y": "21-08-2024",
    "%x": "08/21/24",
    "%m/%d/%Y": "08/21/2024",
    "%m-%d-%y": "08-21-24",
    "%m-%d-%Y": "08-21-2024",
    "%m.%d.%y": "08.21.24",
    "%m.%d.%Y": "08.21.2024",
    "%Y/%m/%d": "2024/08/21",
    "%Y-%m-%d": "2024-08-21",
    "%Y.%m.%d": "2024.08.21",
}


class SettingsPanel(PanelWidget):
    driver: "QtDriver"

    def __init__(self, driver: "QtDriver"):
        super().__init__()
        # set these "constants" because language will be loaded from config shortly after startup
        # and we want to use the current language for the dropdowns
        global FILEPATH_OPTION_MAP, THEME_MAP, TAG_CLICK_ACTION_MAP
        FILEPATH_OPTION_MAP = {
            ShowFilepathOption.SHOW_FULL_PATHS: Translations["settings.filepath.option.full"],
            ShowFilepathOption.SHOW_RELATIVE_PATHS: Translations[
                "settings.filepath.option.relative"
            ],
            ShowFilepathOption.SHOW_FILENAMES_ONLY: Translations["settings.filepath.option.name"],
        }
        THEME_MAP = {
            Theme.DARK: Translations["settings.theme.dark"],
            Theme.LIGHT: Translations["settings.theme.light"],
            Theme.SYSTEM: Translations["settings.theme.system"],
        }
        TAG_CLICK_ACTION_MAP = {
            TagClickActionOption.OPEN_EDIT: Translations["settings.tag_click_action.open_edit"],
            TagClickActionOption.SET_SEARCH: Translations["settings.tag_click_action.set_search"],
            TagClickActionOption.ADD_TO_SEARCH: Translations[
                "settings.tag_click_action.add_to_search"
            ],
        }

        self.driver = driver
        self.setMinimumSize(400, 300)

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 6, 0, 0)

        # Tabs
        self.tab_widget = QTabWidget()

        self.__build_global_settings()
        self.tab_widget.addTab(self.global_settings_container, Translations["settings.global"])

        # self.__build_library_settings()
        # self.tab_widget.addTab(self.library_settings_container, Translations["settings.library"])

        self.root_layout.addWidget(self.tab_widget)

        # Restart Label
        self.restart_label = QLabel(Translations["settings.restart_required"])
        self.restart_label.setHidden(True)
        self.restart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.root_layout.addStretch(1)
        self.root_layout.addWidget(self.restart_label)

        self.__update_restart_label()

    def __update_restart_label(self):
        show_label = (
            self.language_combobox.currentData() != Translations.current_language
            or self.theme_combobox.currentData() != self.driver.applied_theme
        )
        self.restart_label.setHidden(not show_label)

    def __build_global_settings(self):
        self.global_settings_container = QWidget()
        form_layout = QFormLayout(self.global_settings_container)
        form_layout.setContentsMargins(6, 6, 6, 6)

        # Language
        self.language_combobox = QComboBox()
        for k in LANGUAGES:
            self.language_combobox.addItem(k, LANGUAGES[k])
        current_lang: str = self.driver.settings.language
        if current_lang not in LANGUAGES.values():
            current_lang = DEFAULT_TRANSLATION
        self.language_combobox.setCurrentIndex(list(LANGUAGES.values()).index(current_lang))
        self.language_combobox.currentIndexChanged.connect(self.__update_restart_label)
        form_layout.addRow(Translations["settings.language"], self.language_combobox)

        # Open Last Library on Start
        self.open_last_lib_checkbox = QCheckBox()
        self.open_last_lib_checkbox.setChecked(self.driver.settings.open_last_loaded_on_startup)
        form_layout.addRow(
            Translations["settings.open_library_on_start"], self.open_last_lib_checkbox
        )

        # Autoplay
        self.autoplay_checkbox = QCheckBox()
        self.autoplay_checkbox.setChecked(self.driver.settings.autoplay)
        form_layout.addRow(Translations["media_player.autoplay"], self.autoplay_checkbox)

        # Show Filenames in Grid
        self.show_filenames_checkbox = QCheckBox()
        self.show_filenames_checkbox.setChecked(self.driver.settings.show_filenames_in_grid)
        form_layout.addRow(
            Translations["settings.show_filenames_in_grid"], self.show_filenames_checkbox
        )

        # Page Size
        self.page_size_line_edit = QLineEdit()
        self.page_size_line_edit.setText(str(self.driver.settings.page_size))

        def on_page_size_changed():
            text = self.page_size_line_edit.text()
            if not text.isdigit() or int(text) < 1:
                self.page_size_line_edit.setText(str(self.driver.settings.page_size))

        self.page_size_line_edit.editingFinished.connect(on_page_size_changed)
        form_layout.addRow(Translations["settings.page_size"], self.page_size_line_edit)

        # Show Filepath
        self.filepath_combobox = QComboBox()
        for k in FILEPATH_OPTION_MAP:
            self.filepath_combobox.addItem(FILEPATH_OPTION_MAP[k], k)
        filepath_option: ShowFilepathOption = self.driver.settings.show_filepath
        if filepath_option not in FILEPATH_OPTION_MAP:
            filepath_option = ShowFilepathOption.DEFAULT
        self.filepath_combobox.setCurrentIndex(
            list(FILEPATH_OPTION_MAP.keys()).index(filepath_option)
        )
        form_layout.addRow(Translations["settings.filepath.label"], self.filepath_combobox)

        # Dark Mode
        self.theme_combobox = QComboBox()
        for k in THEME_MAP:
            self.theme_combobox.addItem(THEME_MAP[k], k)
        theme = self.driver.settings.theme
        if theme not in THEME_MAP:
            theme = Theme.DEFAULT
        self.theme_combobox.setCurrentIndex(list(THEME_MAP.keys()).index(theme))
        self.theme_combobox.currentIndexChanged.connect(self.__update_restart_label)
        form_layout.addRow(Translations["settings.theme.label"], self.theme_combobox)

        # Tag Click Action
        self.tag_click_action_combobox = QComboBox()
        for k in TAG_CLICK_ACTION_MAP:
            self.tag_click_action_combobox.addItem(TAG_CLICK_ACTION_MAP[k], k)
        tag_click_action = self.driver.settings.tag_click_action
        if tag_click_action not in TAG_CLICK_ACTION_MAP:
            tag_click_action = TagClickActionOption.DEFAULT
        self.tag_click_action_combobox.setCurrentIndex(
            list(TAG_CLICK_ACTION_MAP.keys()).index(tag_click_action)
        )
        form_layout.addRow(
            Translations["settings.tag_click_action.label"], self.tag_click_action_combobox
        )

        # Date Format
        self.dateformat_combobox = QComboBox()
        for k in DATE_FORMAT_MAP:
            self.dateformat_combobox.addItem(DATE_FORMAT_MAP[k], k)
        dateformat: str = self.driver.settings.date_format
        if dateformat not in DATE_FORMAT_MAP:
            dateformat = "%x"
        self.dateformat_combobox.setCurrentIndex(list(DATE_FORMAT_MAP.keys()).index(dateformat))
        self.dateformat_combobox.currentIndexChanged.connect(self.__update_restart_label)
        form_layout.addRow(Translations["settings.dateformat.label"], self.dateformat_combobox)

        # 24-Hour Format
        self.hourformat_checkbox = QCheckBox()
        self.hourformat_checkbox.setChecked(self.driver.settings.hour_format)
        form_layout.addRow(Translations["settings.hourformat.label"], self.hourformat_checkbox)

        # Zero-padding
        self.zeropadding_checkbox = QCheckBox()
        self.zeropadding_checkbox.setChecked(self.driver.settings.zero_padding)
        form_layout.addRow(Translations["settings.zeropadding.label"], self.zeropadding_checkbox)

    def __build_library_settings(self):
        self.library_settings_container = QWidget()
        form_layout = QFormLayout(self.library_settings_container)
        form_layout.setContentsMargins(6, 6, 6, 6)

        todo_label = QLabel("TODO")
        form_layout.addRow(todo_label)

    def __get_language(self) -> str:
        return list(LANGUAGES.values())[self.language_combobox.currentIndex()]

    def get_settings(self) -> dict:
        return {
            "language": self.__get_language(),
            "open_last_loaded_on_startup": self.open_last_lib_checkbox.isChecked(),
            "autoplay": self.autoplay_checkbox.isChecked(),
            "show_filenames_in_grid": self.show_filenames_checkbox.isChecked(),
            "page_size": int(self.page_size_line_edit.text()),
            "show_filepath": self.filepath_combobox.currentData(),
            "theme": self.theme_combobox.currentData(),
            "tag_click_action": self.tag_click_action_combobox.currentData(),
            "date_format": self.dateformat_combobox.currentData(),
            "hour_format": self.hourformat_checkbox.isChecked(),
            "zero_padding": self.zeropadding_checkbox.isChecked(),
        }

    def update_settings(self, driver: "QtDriver"):
        settings = self.get_settings()

        driver.settings.language = settings["language"]
        driver.settings.open_last_loaded_on_startup = settings["open_last_loaded_on_startup"]
        driver.settings.autoplay = settings["autoplay"]
        driver.settings.show_filenames_in_grid = settings["show_filenames_in_grid"]
        driver.settings.page_size = settings["page_size"]
        driver.settings.show_filepath = settings["show_filepath"]
        driver.settings.theme = settings["theme"]
        driver.settings.tag_click_action = settings["tag_click_action"]
        driver.settings.date_format = settings["date_format"]
        driver.settings.hour_format = settings["hour_format"]
        driver.settings.zero_padding = settings["zero_padding"]

        driver.settings.save()

        # Apply changes
        # Show File Path
        driver.update_recent_lib_menu()
        driver.main_window.preview_panel.set_selection(self.driver.selected)
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
            window_title=Translations["settings.title"],
            done_callback=lambda: settings_panel.update_settings(driver),
            has_save=True,
        )
        modal.title_widget.setVisible(False)

        return modal
