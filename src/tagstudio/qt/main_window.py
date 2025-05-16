# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import typing
from pathlib import Path

import structlog
from PySide6 import QtCore
from PySide6.QtCore import QMetaObject, QSize, QStringListModel, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QCompleter,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLayout,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMenuBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from tagstudio.core.enums import ShowFilepathOption
from tagstudio.qt.pagination import Pagination
from tagstudio.qt.platform_strings import trash_term
from tagstudio.qt.translations import Translations
from tagstudio.qt.widgets.landing import LandingWidget
from tagstudio.qt.widgets.preview_panel import PreviewPanel

# Only import for type checking/autocompletion, will not be imported at runtime.
if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver


logger = structlog.get_logger(__name__)


class MainMenuBar(QMenuBar):
    file_menu: QMenu
    open_library_action: QAction
    open_recent_library_menu: QMenu
    save_library_backup_action: QAction
    settings_action: QAction
    open_on_start_action: QAction
    refresh_dir_action: QAction
    close_library_action: QAction

    edit_menu: QMenu
    new_tag_action: QAction
    select_all_action: QAction
    select_inverse_action: QAction
    clear_select_action: QAction
    copy_fields_action: QAction
    paste_fields_action: QAction
    add_tag_to_selected_action: QAction
    delete_file_action: QAction
    manage_file_ext_action: QAction
    tag_manager_action: QAction
    color_manager_action: QAction

    view_menu: QMenu
    show_filenames_action: QAction

    def __init__(self, parent=...):
        super().__init__(parent)

        self.setup_file_menu()
        self.setup_edit_menu()
        self.setup_view_menu()

    def setup_file_menu(self):
        self.file_menu = QMenu(Translations["menu.file"], self)

        # Open/Create Library
        self.open_library_action = QAction(Translations["menu.file.open_create_library"], self)
        self.open_library_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_O,
            )
        )
        self.open_library_action.setToolTip("Ctrl+O")
        self.file_menu.addAction(self.open_library_action)

        # Open Recent
        self.open_recent_library_menu = QMenu(Translations["menu.file.open_recent_library"], self)
        self.file_menu.addMenu(self.open_recent_library_menu)

        # Save Library Backup
        self.save_library_backup_action = QAction(Translations["menu.file.save_backup"], self)
        self.save_library_backup_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(
                    QtCore.Qt.KeyboardModifier.ControlModifier
                    | QtCore.Qt.KeyboardModifier.ShiftModifier
                ),
                QtCore.Qt.Key.Key_S,
            )
        )
        self.save_library_backup_action.setStatusTip("Ctrl+Shift+S")
        self.save_library_backup_action.setEnabled(False)
        self.file_menu.addAction(self.save_library_backup_action)

        self.file_menu.addSeparator()

        # Settings...
        self.settings_action = QAction(Translations["menu.settings"], self)
        self.file_menu.addAction(self.settings_action)

        # Open Library on Start
        self.open_on_start_action = QAction(Translations["settings.open_library_on_start"], self)
        self.open_on_start_action.setCheckable(True)
        self.file_menu.addAction(self.open_on_start_action)

        self.file_menu.addSeparator()

        # Refresh Directories
        self.refresh_dir_action = QAction(Translations["menu.file.refresh_directories"], self)
        self.refresh_dir_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_R,
            )
        )
        self.refresh_dir_action.setStatusTip("Ctrl+R")
        self.refresh_dir_action.setEnabled(False)
        self.file_menu.addAction(self.refresh_dir_action)

        self.file_menu.addSeparator()

        # Close Library
        self.close_library_action = QAction(Translations["menu.file.close_library"], self)
        self.close_library_action.setEnabled(False)
        self.file_menu.addAction(self.close_library_action)

        self.file_menu.addSeparator()

        self.addMenu(self.file_menu)

    def setup_edit_menu(self):
        self.edit_menu = QMenu(Translations["generic.edit_alt"], self)

        # New Tag
        self.new_tag_action = QAction(Translations["menu.edit.new_tag"], self)
        self.new_tag_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_T,
            )
        )
        self.new_tag_action.setToolTip("Ctrl+T")
        self.new_tag_action.setEnabled(False)
        self.edit_menu.addAction(self.new_tag_action)

        self.edit_menu.addSeparator()

        # Select All
        self.select_all_action = QAction(Translations["select.all"], self)
        self.select_all_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_A,
            )
        )
        self.select_all_action.setToolTip("Ctrl+A")
        self.select_all_action.setEnabled(False)
        self.edit_menu.addAction(self.select_all_action)

        # Invert Selection
        self.select_inverse_action = QAction(Translations["select.inverse"], self)
        self.select_inverse_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(
                    QtCore.Qt.KeyboardModifier.ControlModifier
                    ^ QtCore.Qt.KeyboardModifier.ShiftModifier
                ),
                QtCore.Qt.Key.Key_I,
            )
        )
        self.select_inverse_action.setToolTip("Ctrl+Shift+I")
        self.select_inverse_action.setEnabled(False)
        self.edit_menu.addAction(self.select_inverse_action)

        # Clear Selection
        self.clear_select_action = QAction(Translations["select.clear"], self)
        self.clear_select_action.setShortcut(QtCore.Qt.Key.Key_Escape)
        self.clear_select_action.setToolTip("Esc")
        self.clear_select_action.setEnabled(False)
        self.edit_menu.addAction(self.clear_select_action)

        # Copy Fields
        self.copy_fields_action = QAction(Translations["edit.copy_fields"], self)
        self.copy_fields_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_C,
            )
        )
        self.copy_fields_action.setToolTip("Ctrl+C")
        self.copy_fields_action.setEnabled(False)
        self.edit_menu.addAction(self.copy_fields_action)

        # Paste Fields
        self.paste_fields_action = QAction(Translations["edit.paste_fields"], self)
        self.paste_fields_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_V,
            )
        )
        self.paste_fields_action.setToolTip("Ctrl+V")
        self.paste_fields_action.setEnabled(False)
        self.edit_menu.addAction(self.paste_fields_action)

        # Add Tag to Selected
        self.add_tag_to_selected_action = QAction(Translations["select.add_tag_to_selected"], self)
        self.add_tag_to_selected_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(
                    QtCore.Qt.KeyboardModifier.ControlModifier
                    ^ QtCore.Qt.KeyboardModifier.ShiftModifier
                ),
                QtCore.Qt.Key.Key_T,
            )
        )
        self.add_tag_to_selected_action.setToolTip("Ctrl+Shift+T")
        self.add_tag_to_selected_action.setEnabled(False)
        self.edit_menu.addAction(self.add_tag_to_selected_action)

        self.edit_menu.addSeparator()

        # Move Files to trash
        self.delete_file_action = QAction(
            Translations.format("menu.delete_selected_files_ambiguous", trash_term=trash_term()),
            self,
        )
        self.delete_file_action.setShortcut(QtCore.Qt.Key.Key_Delete)
        self.delete_file_action.setEnabled(False)
        self.edit_menu.addAction(self.delete_file_action)

        self.edit_menu.addSeparator()

        # Manage File Extensions
        self.manage_file_ext_action = QAction(
            Translations["menu.edit.manage_file_extensions"], self
        )
        self.manage_file_ext_action.setEnabled(False)
        self.edit_menu.addAction(self.manage_file_ext_action)

        # Manage Tags
        self.tag_manager_action = QAction(Translations["menu.edit.manage_tags"], self)
        self.tag_manager_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_M,
            )
        )
        self.tag_manager_action.setEnabled(False)
        self.tag_manager_action.setToolTip("Ctrl+M")
        self.edit_menu.addAction(self.tag_manager_action)

        # Color Manager
        self.color_manager_action = QAction(Translations["edit.color_manager"], self)
        self.color_manager_action.setEnabled(False)
        self.edit_menu.addAction(self.color_manager_action)

        self.addMenu(self.edit_menu)

    def setup_view_menu(self):
        self.view_menu = QMenu(Translations["menu.view"], self)

        # show_libs_list_action = QAction(Translations["settings.show_recent_libraries"], menu_bar)
        # show_libs_list_action.setCheckable(True)
        # show_libs_list_action.setChecked(self.settings.show_library_list)

        self.show_filenames_action = QAction(Translations["settings.show_filenames_in_grid"], self)
        self.show_filenames_action.setCheckable(True)
        self.view_menu.addAction(self.show_filenames_action)

        self.addMenu(self.view_menu)

    def rebuild_open_recent_library_menu(
        self,
        libraries: list[Path],
        show_filepath: ShowFilepathOption,
        open_library_callback,
        clear_libraries_callback,
    ):
        actions: list[QAction] = []
        for path in libraries:
            action = QAction(self.open_recent_library_menu)
            if show_filepath == ShowFilepathOption.SHOW_FULL_PATHS:
                action.setText(str(path))
            else:
                action.setText(str(path.name))
            action.triggered.connect(lambda checked=False, p=path: open_library_callback(p))
            actions.append(action)

        clear_recent_action = QAction(
            Translations["menu.file.clear_recent_libraries"], self.open_recent_library_menu
        )
        clear_recent_action.triggered.connect(clear_libraries_callback)
        actions.append(clear_recent_action)

        # Clear previous actions
        for action in self.open_recent_library_menu.actions():
            self.open_recent_library_menu.removeAction(action)

        # Add new actions
        for action in actions:
            self.open_recent_library_menu.addAction(action)

        # Only enable add "clear recent" if there are still recent libraries.
        if len(actions) > 1:
            self.open_recent_library_menu.setDisabled(False)
            self.open_recent_library_menu.addSeparator()
            self.open_recent_library_menu.addAction(clear_recent_action)
        else:
            self.open_recent_library_menu.setDisabled(True)


# View Component
class MainWindow(QMainWindow):
    def __init__(self, driver: "QtDriver", parent=None) -> None:
        super().__init__(parent)

        if not self.objectName():
            self.setObjectName("MainWindow")
        self.resize(1300, 720)

        self.setup_menu_bar()

        self.setup_central_widget(driver)

        self.setup_status_bar()

        QMetaObject.connectSlotsByName(self)

        # NOTE: These are old attempts to allow for a translucent/acrylic
        # window effect. This may be attempted again in the future.
        # self.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)
        # self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, False)
        # # self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # self.windowFX = WindowEffect()
        # self.windowFX.setAcrylicEffect(self.winId(), isEnableShadow=False)

    # region UI Setup Methods

    # region Menu Bar

    def setup_menu_bar(self):
        self.menu_bar = MainMenuBar(self)

        self.setMenuBar(self.menu_bar)
        self.menu_bar.setNativeMenuBar(True)

    # endregion

    def setup_central_widget(self, driver: "QtDriver"):
        self.central_widget = QWidget(self)
        self.central_widget.setObjectName("centralwidget")
        self.central_layout = QGridLayout(self.central_widget)
        self.central_layout.setObjectName("centralLayout")

        self.setup_search_bar()

        self.setup_extra_input_bar()

        self.setup_content(driver)

        self.setCentralWidget(self.central_widget)

    def setup_search_bar(self):
        """Sets up Nav Buttons, Search Field, Search Button."""
        nav_button_style = "font-size:14;font-weight:bold;"
        self.search_bar_layout = QHBoxLayout()
        self.search_bar_layout.setObjectName("search_bar_layout")
        self.search_bar_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        self.back_button = QPushButton("<", self.central_widget)
        self.back_button.setObjectName("backButton")
        self.back_button.setMinimumSize(QSize(0, 32))
        self.back_button.setMaximumSize(QSize(32, 16777215))
        self.back_button.setStyleSheet(nav_button_style)
        self.search_bar_layout.addWidget(self.back_button)

        self.forward_button = QPushButton(">", self.central_widget)
        self.forward_button.setObjectName("forwardButton")
        self.forward_button.setMinimumSize(QSize(0, 32))
        self.forward_button.setMaximumSize(QSize(32, 16777215))
        self.forward_button.setStyleSheet(nav_button_style)
        self.search_bar_layout.addWidget(self.forward_button)

        self.search_field = QLineEdit(self.central_widget)
        self.search_field.setPlaceholderText(Translations["home.search_entries"])
        self.search_field.setObjectName("searchField")
        self.search_field.setMinimumSize(QSize(0, 32))
        self.search_field_completion_list = QStringListModel()
        self.search_field_completer = QCompleter(
            self.search_field_completion_list, self.search_field
        )
        self.search_field_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.search_field.setCompleter(self.search_field_completer)
        self.search_bar_layout.addWidget(self.search_field)

        self.search_button = QPushButton(Translations["home.search"], self.central_widget)
        self.search_button.setObjectName("searchButton")
        self.search_button.setMinimumSize(QSize(0, 32))
        self.search_bar_layout.addWidget(self.search_button)

        self.central_layout.addLayout(self.search_bar_layout, 3, 0, 1, 1)

    def setup_extra_input_bar(self):
        """Sets up inputs for sorting settings and thumbnail size."""
        self.extra_input_layout = QHBoxLayout()
        self.extra_input_layout.setObjectName("extra_input_layout")

        ## left side spacer
        self.extra_input_layout.addItem(
            QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        ## Sorting Dropdowns
        self.sorting_mode_combobox = QComboBox(self.central_widget)
        self.sorting_mode_combobox.setObjectName("sortingModeComboBox")
        self.extra_input_layout.addWidget(self.sorting_mode_combobox)

        self.sorting_direction_combobox = QComboBox(self.central_widget)
        self.sorting_direction_combobox.setObjectName("sortingDirectionCombobox")
        self.extra_input_layout.addWidget(self.sorting_direction_combobox)

        ## Thumbnail Size placeholder
        self.thumb_size_combobox = QComboBox(self.central_widget)
        self.thumb_size_combobox.setObjectName("thumbSizeComboBox")
        self.thumb_size_combobox.setPlaceholderText(Translations["home.thumbnail_size"])
        self.thumb_size_combobox.setCurrentText("")
        size_policy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.thumb_size_combobox.sizePolicy().hasHeightForWidth())
        self.thumb_size_combobox.setSizePolicy(size_policy)
        self.thumb_size_combobox.setMinimumWidth(128)
        self.thumb_size_combobox.setMaximumWidth(352)
        self.extra_input_layout.addWidget(self.thumb_size_combobox)

        self.central_layout.addLayout(self.extra_input_layout, 5, 0, 1, 1)

    def setup_content(self, driver: "QtDriver"):
        self.content_layout = QHBoxLayout()
        self.content_layout.setObjectName("horizontalLayout")

        self.content_splitter = QSplitter()
        self.content_splitter.setObjectName("splitter")
        self.content_splitter.setHandleWidth(12)

        self.setup_entry_list(driver)

        self.setup_preview_panel(driver)

        self.content_splitter.setStretchFactor(0, 1)
        self.content_layout.addWidget(self.content_splitter)

        self.central_layout.addLayout(self.content_layout, 10, 0, 1, 1)

    def setup_entry_list(self, driver: "QtDriver"):
        self.entry_list_container = QWidget()
        self.entry_list_layout = QVBoxLayout(self.entry_list_container)
        self.entry_list_layout.setSpacing(0)

        self.entry_scroll_area = QScrollArea()
        self.entry_scroll_area.setObjectName("scrollArea")
        self.entry_scroll_area.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        self.entry_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.entry_scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.entry_scroll_area.setWidgetResizable(True)
        self.entry_list_layout.addWidget(self.entry_scroll_area)

        self.landing_widget: LandingWidget = LandingWidget(driver, self.devicePixelRatio())
        self.entry_list_layout.addWidget(self.landing_widget)

        self.pagination = Pagination()
        self.entry_list_layout.addWidget(self.pagination)
        self.content_splitter.addWidget(self.entry_list_container)

    def setup_preview_panel(self, driver: "QtDriver"):
        self.preview_panel = PreviewPanel(driver.lib, driver)
        self.content_splitter.addWidget(self.preview_panel)

    def setup_status_bar(self):
        self.status_bar = QStatusBar(self)
        self.status_bar.setObjectName("statusbar")
        status_bar_size_policy = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
        )
        status_bar_size_policy.setHorizontalStretch(0)
        status_bar_size_policy.setVerticalStretch(0)
        status_bar_size_policy.setHeightForWidth(self.status_bar.sizePolicy().hasHeightForWidth())
        self.status_bar.setSizePolicy(status_bar_size_policy)
        self.status_bar.setSizeGripEnabled(False)
        self.setStatusBar(self.status_bar)

    # endregion

    def moveEvent(self, event) -> None:  # noqa: N802
        # time.sleep(0.02)  # sleep for 20ms
        pass

    def resizeEvent(self, event) -> None:  # noqa: N802
        # time.sleep(0.02)  # sleep for 20ms
        pass

    def toggle_landing_page(self, enabled: bool):
        if enabled:
            self.entry_scroll_area.setHidden(True)
            self.landing_widget.setHidden(False)
            self.landing_widget.animate_logo_in()
        else:
            self.landing_widget.setHidden(True)
            self.landing_widget.set_status_label("")
            self.entry_scroll_area.setHidden(False)
