import webbrowser
from pathlib import Path

from PySide6 import QtCore
from PySide6.QtCore import Signal
from PySide6.QtGui import (
    QAction,
)
from PySide6.QtWidgets import (
    QMenu,
    QMenuBar,
)
from src.core.enums import SettingItems
from src.qt.modals.build_tag import BuildTagPanel
from src.qt.modals.file_extension import FileExtensionModal
from src.qt.modals.fix_dupes import FixDupeFilesModal
from src.qt.modals.fix_unlinked import FixUnlinkedEntriesModal
from src.qt.modals.folders_to_tags import FoldersToTagsModal
from src.qt.translations import Translations
from src.qt.widgets.panel import PanelModal


class MenuBar(QMenuBar):
    """Menubar for the main window."""

    create_library_modal_signal = Signal()
    open_library_signal = Signal(Path)
    backup_library_signal = Signal()
    refresh_directories_signal = Signal()
    close_library_signal = Signal()
    select_all_items_signal = Signal()
    clear_selection_signal = Signal()
    filter_items_signal = Signal()
    tag_database_modal_signal = Signal()
    show_grid_filenames_signal = Signal(bool)
    autofill_macro_signal = Signal()

    def __init__(self, parent, settings, lib, driver):
        super().__init__(parent)
        self.settings = settings
        self.lib = lib
        self.driver = driver

        self.setNativeMenuBar(True)

        self.file_menu = QMenu(self)
        Translations.translate_qobject(self.file_menu, "menu.file")
        self.edit_menu = QMenu(self)
        Translations.translate_qobject(self.edit_menu, "generic.edit_alt")
        self.view_menu = QMenu(self)
        Translations.translate_qobject(self.view_menu, "menu.view")
        self.tools_menu = QMenu(self)
        Translations.translate_qobject(self.tools_menu, "menu.tools")
        self.macros_menu = QMenu(self)
        Translations.translate_qobject(self.macros_menu, "menu.macros")
        self.help_menu = QMenu(self)
        Translations.translate_qobject(self.help_menu, "menu.help")

        # File Menu ============================================================
        self.open_library_action = QAction(self)
        Translations.translate_qobject(self.open_library_action, "menu.file.open_create_library")
        self.open_library_action.triggered.connect(lambda: self.create_library_modal_signal.emit())

        self.open_library_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_O,
            )
        )
        self.open_library_action.setToolTip("Ctrl+O")
        self.file_menu.addAction(self.open_library_action)

        self.open_recent_action = QMenu(self)
        Translations.translate_qobject(self.open_recent_action, "menu.file.open_recent_library")
        self.file_menu.addMenu(self.open_recent_action)
        self.update_recent_lib_menu()

        self.open_on_start_action = QAction(self)
        Translations.translate_qobject(self.open_on_start_action, "settings.open_library_on_start")
        self.open_on_start_action.setCheckable(True)
        self.open_on_start_action.setChecked(
            bool(self.settings.value(SettingItems.START_LOAD_LAST, defaultValue=True, type=bool))
        )
        self.open_on_start_action.triggered.connect(
            lambda checked: self.settings.setValue(SettingItems.START_LOAD_LAST, checked)
        )
        self.file_menu.addAction(self.open_on_start_action)

        self.file_menu.addSeparator()

        self.save_library_backup_action = QAction(self)
        Translations.translate_qobject(self.save_library_backup_action, "menu.file.save_backup")
        self.save_library_backup_action.triggered.connect(lambda: self.backup_library_signal.emit())
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
        self.file_menu.addAction(self.save_library_backup_action)

        self.file_menu.addSeparator()

        self.refresh_directories_action = QAction(self)
        Translations.translate_qobject(
            self.refresh_directories_action, "menu.file.refresh_directories"
        )
        self.refresh_directories_action.triggered.connect(
            lambda: self.refresh_directories_signal.emit()
        )
        self.refresh_directories_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_R,
            )
        )
        self.refresh_directories_action.setStatusTip("Ctrl+R")
        self.file_menu.addAction(self.refresh_directories_action)
        self.file_menu.addSeparator()

        self.close_library_action = QAction(self)
        Translations.translate_qobject(self.close_library_action, "menu.file.close_library")
        self.close_library_action.triggered.connect(lambda: self.close_library_signal.emit())
        self.file_menu.addAction(self.close_library_action)
        self.file_menu.addSeparator()

        # Edit Menu ============================================================
        self.new_tag_action = QAction(self)
        Translations.translate_qobject(self.new_tag_action, "menu.edit.new_tag")
        self.new_tag_action.triggered.connect(self._open_add_tag_modal)
        self.new_tag_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_T,
            )
        )
        self.new_tag_action.setToolTip("Ctrl+T")
        self.edit_menu.addAction(self.new_tag_action)

        self.edit_menu.addSeparator()

        self.select_all_action = QAction(self)
        Translations.translate_qobject(self.select_all_action, "select.all")
        self.select_all_action.triggered.connect(lambda: self.select_all_items_signal.emit())
        self.select_all_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_A,
            )
        )
        self.select_all_action.setToolTip("Ctrl+A")
        self.edit_menu.addAction(self.select_all_action)

        self.clear_select_action = QAction(self)
        Translations.translate_qobject(self.clear_select_action, "select.clear")
        self.clear_select_action.triggered.connect(lambda: self.clear_selection_signal.emit())
        self.clear_select_action.setShortcut(QtCore.Qt.Key.Key_Escape)
        self.clear_select_action.setToolTip("Esc")
        self.edit_menu.addAction(self.clear_select_action)

        self.edit_menu.addSeparator()

        self.manage_file_extensions_action = QAction(self)
        Translations.translate_qobject(
            self.manage_file_extensions_action, "menu.edit.manage_file_extensions"
        )
        self.manage_file_extensions_action.triggered.connect(self._open_file_extension_modal)
        self.edit_menu.addAction(self.manage_file_extensions_action)

        self.tag_database_action = QAction(self)
        Translations.translate_qobject(self.tag_database_action, "menu.edit.manage_tags")
        self.tag_database_action.triggered.connect(lambda: self.tag_database_modal_signal.emit())
        self.edit_menu.addAction(self.tag_database_action)

        # View Menu ============================================================
        self.show_libs_list_action = QAction(self)
        Translations.translate_qobject(self.show_libs_list_action, "settings.show_recent_libraries")
        self.show_libs_list_action.setCheckable(True)
        self.show_libs_list_action.setChecked(
            bool(self.settings.value(SettingItems.WINDOW_SHOW_LIBS, defaultValue=True, type=bool))
        )
        self.view_menu.addAction(self.show_libs_list_action)

        self.show_filenames_action = QAction(self)
        Translations.translate_qobject(
            self.show_filenames_action, "settings.show_filenames_in_grid"
        )
        self.show_filenames_action.setCheckable(True)
        self.show_filenames_action.setChecked(
            bool(self.settings.value(SettingItems.SHOW_FILENAMES, defaultValue=True, type=bool))
        )
        self.show_filenames_action.triggered.connect(
            lambda checked: (
                self.settings.setValue(SettingItems.SHOW_FILENAMES, checked),
                self.show_grid_filenames_signal.emit(checked),
            )
        )
        self.view_menu.addAction(self.show_filenames_action)

        # Tools Menu ===========================================================
        self.fix_unlinked_entries_action = QAction(self)
        Translations.translate_qobject(
            self.fix_unlinked_entries_action, "menu.tools.fix_unlinked_entries"
        )
        self.fix_unlinked_entries_action.triggered.connect(self._open_fix_unlinked_entries_modal)
        self.tools_menu.addAction(self.fix_unlinked_entries_action)

        self.fix_dupe_files_action = QAction(self)
        Translations.translate_qobject(self.fix_dupe_files_action, "menu.tools.fix_duplicate_files")
        self.fix_dupe_files_action.triggered.connect(self._open_dupe_files_modal)
        self.tools_menu.addAction(self.fix_dupe_files_action)

        # create_collage_action = QAction("Create Collage", self)
        # create_collage_action.triggered.connect(lambda: self.create_collage())
        # tools_menu.addAction(create_collage_action)

        # Macros Menu ==========================================================
        self.autofill_action = QAction("Autofill", self)
        self.autofill_action.triggered.connect(lambda: self.autofill_macro_signal.emit())
        self.macros_menu.addAction(self.autofill_action)

        self.folders_to_tags_action = QAction(self)
        Translations.translate_qobject(self.folders_to_tags_action, "menu.macros.folders_to_tags")
        self.folders_to_tags_action.triggered.connect(self._open_folders_to_tags_modal)
        self.macros_menu.addAction(self.folders_to_tags_action)

        # Help Menu ============================================================
        self.repo_action = QAction(self)
        Translations.translate_qobject(self.repo_action, "help.visit_github")
        self.repo_action.triggered.connect(
            lambda: webbrowser.open("https://github.com/TagStudioDev/TagStudio")
        )
        self.help_menu.addAction(self.repo_action)

        self.addMenu(self.file_menu)
        self.addMenu(self.edit_menu)
        self.addMenu(self.view_menu)
        self.addMenu(self.tools_menu)
        self.addMenu(self.macros_menu)
        self.addMenu(self.help_menu)

    def _open_folders_to_tags_modal(self):
        if not hasattr(self, "folders_modal"):
            self.folders_modal = FoldersToTagsModal(self.lib, self.driver)
        self.folders_modal.show()

    def _open_add_tag_modal(self):
        panel = BuildTagPanel(self.lib)
        self.modal = PanelModal(
            panel,
            has_save=True,
        )
        Translations.translate_with_setter(self.modal.setTitle, "tag.new")
        Translations.translate_with_setter(self.modal.setWindowTitle, "tag.add")

        self.modal.saved.connect(
            lambda: (
                self.lib.add_tag(
                    panel.build_tag(),
                    set(panel.parent_ids),
                    set(panel.alias_names),
                    set(panel.alias_ids),
                ),
                self.modal.hide(),
            )
        )
        self.modal.show()

    def _open_file_extension_modal(self):
        panel = FileExtensionModal(self.lib)
        self.modal = PanelModal(
            panel,
            has_save=True,
        )
        Translations.translate_with_setter(self.modal.setTitle, "ignore_list.title")
        Translations.translate_with_setter(self.modal.setWindowTitle, "ignore_list.title")

        self.modal.saved.connect(lambda: (panel.save(), self.filter_items_signal.emit()))
        self.modal.show()

    def _open_fix_unlinked_entries_modal(self):
        if not hasattr(self, "unlinked_modal"):
            self.unlinked_modal = FixUnlinkedEntriesModal(self.lib, self.driver)
        self.unlinked_modal.show()

    def _open_dupe_files_modal(self):
        if not hasattr(self, "dupe_modal"):
            self.dupe_modal = FixDupeFilesModal(self.lib, self.driver)
        self.dupe_modal.show()

    def _clear_recent_libs(self):
        """Clear the list of recent libraries from the settings file."""
        settings = self.settings
        settings.beginGroup(SettingItems.LIBS_LIST)
        self.settings.remove("")
        self.settings.endGroup()
        self.settings.sync()
        self.update_recent_lib_menu()

    def set_library_actions_disabled(self, value: bool):
        actions: list[QAction] = [
            self.save_library_backup_action,
            self.refresh_directories_action,
            self.close_library_action,
            self.new_tag_action,
            self.select_all_action,
            self.clear_select_action,
            self.manage_file_extensions_action,
            self.tag_database_action,
            self.fix_unlinked_entries_action,
            self.fix_dupe_files_action,
        ]
        for action in actions:
            action.setDisabled(value)

    def set_macro_actions_disabled(self, value: bool):
        self.autofill_action.setDisabled(value)
        self.folders_to_tags_action.setDisabled(value)

    def update_recent_lib_menu(self):
        """Updates the recent library menu from the latest values from the settings file."""
        actions: list[QAction] = []
        lib_items: dict[str, tuple[str, str]] = {}

        settings = self.settings
        settings.beginGroup(SettingItems.LIBS_LIST)
        for item_tstamp in settings.allKeys():
            val = str(settings.value(item_tstamp, type=str))
            cut_val = val
            if len(val) > 45:
                cut_val = f"{val[0:10]} ... {val[-10:]}"
            lib_items[item_tstamp] = (val, cut_val)

        # Sort lib_items by the key
        libs_sorted = sorted(lib_items.items(), key=lambda item: item[0], reverse=True)
        settings.endGroup()

        # Create actions for each library
        for library_key in libs_sorted:
            path = Path(library_key[1][0])
            action = QAction(self.open_recent_action)
            action.setText(str(path))
            action.triggered.connect(lambda checked=False, p=path: self.open_library_signal.emit(p))
            actions.append(action)

        clear_recent_action = QAction(self.open_recent_action)
        Translations.translate_qobject(clear_recent_action, "menu.file.clear_recent_libraries")
        clear_recent_action.triggered.connect(self._clear_recent_libs)
        actions.append(clear_recent_action)

        # Clear previous actions
        for action in self.open_recent_action.actions():
            self.open_recent_action.removeAction(action)

        # Add new actions
        for action in actions:
            self.open_recent_action.addAction(action)

        # Only enable add "clear recent" if there are still recent libraries.
        if len(actions) > 1:
            self.open_recent_action.setDisabled(False)
            self.open_recent_action.addSeparator()
            self.open_recent_action.addAction(clear_recent_action)
        else:
            self.open_recent_action.setDisabled(True)
