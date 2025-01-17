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

        file_menu = QMenu(self)
        Translations.translate_qobject(file_menu, "menu.file")
        edit_menu = QMenu(self)
        Translations.translate_qobject(edit_menu, "generic.edit_alt")
        view_menu = QMenu(self)
        Translations.translate_qobject(view_menu, "menu.view")
        tools_menu = QMenu(self)
        Translations.translate_qobject(tools_menu, "menu.tools")
        macros_menu = QMenu(self)
        Translations.translate_qobject(macros_menu, "menu.macros")
        help_menu = QMenu(self)
        Translations.translate_qobject(help_menu, "menu.help")

        # File Menu ============================================================
        open_library_action = QAction(self)
        Translations.translate_qobject(open_library_action, "menu.file.open_create_library")
        open_library_action.triggered.connect(lambda: self.create_library_modal_signal.emit())

        open_library_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_O,
            )
        )
        open_library_action.setToolTip("Ctrl+O")
        file_menu.addAction(open_library_action)

        self.open_recent_library_menu = QMenu(self)
        Translations.translate_qobject(
            self.open_recent_library_menu, "menu.file.open_recent_library"
        )
        file_menu.addMenu(self.open_recent_library_menu)
        self.update_recent_lib_menu()

        open_on_start_action = QAction(self)
        Translations.translate_qobject(open_on_start_action, "settings.open_library_on_start")
        open_on_start_action.setCheckable(True)
        open_on_start_action.setChecked(
            bool(self.settings.value(SettingItems.START_LOAD_LAST, defaultValue=True, type=bool))
        )
        open_on_start_action.triggered.connect(
            lambda checked: self.settings.setValue(SettingItems.START_LOAD_LAST, checked)
        )
        file_menu.addAction(open_on_start_action)

        file_menu.addSeparator()

        save_library_backup_action = QAction(self)
        Translations.translate_qobject(save_library_backup_action, "menu.file.save_backup")
        save_library_backup_action.triggered.connect(lambda: self.backup_library_signal.emit())
        save_library_backup_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(
                    QtCore.Qt.KeyboardModifier.ControlModifier
                    | QtCore.Qt.KeyboardModifier.ShiftModifier
                ),
                QtCore.Qt.Key.Key_S,
            )
        )
        save_library_backup_action.setStatusTip("Ctrl+Shift+S")
        file_menu.addAction(save_library_backup_action)

        file_menu.addSeparator()

        refresh_directories_action = QAction(self)
        Translations.translate_qobject(refresh_directories_action, "menu.file.refresh_directories")
        refresh_directories_action.triggered.connect(lambda: self.refresh_directories_signal.emit())
        refresh_directories_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_R,
            )
        )
        refresh_directories_action.setStatusTip("Ctrl+R")
        file_menu.addAction(refresh_directories_action)
        file_menu.addSeparator()

        close_library_action = QAction(self)
        Translations.translate_qobject(close_library_action, "menu.file.close_library")
        close_library_action.triggered.connect(lambda: self.close_library_signal.emit())
        file_menu.addAction(close_library_action)
        file_menu.addSeparator()

        # Edit Menu ============================================================
        new_tag_action = QAction(self)
        Translations.translate_qobject(new_tag_action, "menu.edit.new_tag")
        new_tag_action.triggered.connect(self._open_add_tag_modal)
        new_tag_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_T,
            )
        )
        new_tag_action.setToolTip("Ctrl+T")
        edit_menu.addAction(new_tag_action)

        edit_menu.addSeparator()

        select_all_action = QAction(self)
        Translations.translate_qobject(select_all_action, "select.all")
        select_all_action.triggered.connect(lambda: self.select_all_items_signal.emit())
        select_all_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_A,
            )
        )
        select_all_action.setToolTip("Ctrl+A")
        edit_menu.addAction(select_all_action)

        clear_select_action = QAction(self)
        Translations.translate_qobject(clear_select_action, "select.clear")
        clear_select_action.triggered.connect(lambda: self.clear_selection_signal.emit())
        clear_select_action.setShortcut(QtCore.Qt.Key.Key_Escape)
        clear_select_action.setToolTip("Esc")
        edit_menu.addAction(clear_select_action)

        edit_menu.addSeparator()

        manage_file_extensions_action = QAction(self)
        Translations.translate_qobject(
            manage_file_extensions_action, "menu.edit.manage_file_extensions"
        )
        manage_file_extensions_action.triggered.connect(self._open_file_extension_modal)
        edit_menu.addAction(manage_file_extensions_action)

        tag_database_action = QAction(self)
        Translations.translate_qobject(tag_database_action, "menu.edit.manage_tags")
        tag_database_action.triggered.connect(lambda: self.tag_database_modal_signal.emit())
        edit_menu.addAction(tag_database_action)

        # View Menu ============================================================
        show_libs_list_action = QAction(self)
        Translations.translate_qobject(show_libs_list_action, "settings.show_recent_libraries")
        show_libs_list_action.setCheckable(True)
        show_libs_list_action.setChecked(
            bool(self.settings.value(SettingItems.WINDOW_SHOW_LIBS, defaultValue=True, type=bool))
        )

        show_filenames_action = QAction(self)
        Translations.translate_qobject(show_filenames_action, "settings.show_filenames_in_grid")
        show_filenames_action.setCheckable(True)
        show_filenames_action.setChecked(
            bool(self.settings.value(SettingItems.SHOW_FILENAMES, defaultValue=True, type=bool))
        )
        show_filenames_action.triggered.connect(
            lambda checked: (
                self.settings.setValue(SettingItems.SHOW_FILENAMES, checked),
                self.show_grid_filenames_signal.emit(checked),
            )
        )
        view_menu.addAction(show_filenames_action)

        # Tools Menu ===========================================================
        fix_unlinked_entries_action = QAction(self)
        Translations.translate_qobject(
            fix_unlinked_entries_action, "menu.tools.fix_unlinked_entries"
        )
        fix_unlinked_entries_action.triggered.connect(self._open_fix_unlinked_entries_modal)
        tools_menu.addAction(fix_unlinked_entries_action)

        fix_dupe_files_action = QAction(self)
        Translations.translate_qobject(fix_dupe_files_action, "menu.tools.fix_duplicate_files")
        fix_dupe_files_action.triggered.connect(self._open_dupe_files_modal)
        tools_menu.addAction(fix_dupe_files_action)

        # create_collage_action = QAction("Create Collage", self)
        # create_collage_action.triggered.connect(lambda: self.create_collage())
        # tools_menu.addAction(create_collage_action)

        # Macros Menu ==========================================================
        self.autofill_action = QAction("Autofill", self)
        self.autofill_action.triggered.connect(lambda: self.autofill_macro_signal.emit())
        macros_menu.addAction(self.autofill_action)

        folders_to_tags_action = QAction(self)
        Translations.translate_qobject(folders_to_tags_action, "menu.macros.folders_to_tags")
        folders_to_tags_action.triggered.connect(self._open_folders_to_tags_modal)
        macros_menu.addAction(folders_to_tags_action)

        # Help Menu ============================================================
        self.repo_action = QAction(self)
        Translations.translate_qobject(self.repo_action, "help.visit_github")
        self.repo_action.triggered.connect(
            lambda: webbrowser.open("https://github.com/TagStudioDev/TagStudio")
        )
        help_menu.addAction(self.repo_action)

        self.addMenu(file_menu)
        self.addMenu(edit_menu)
        self.addMenu(view_menu)
        self.addMenu(tools_menu)
        self.addMenu(macros_menu)
        self.addMenu(help_menu)

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

    def set_macro_menu_viability(self, value: bool):
        self.autofill_action.setDisabled(value)

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
            action = QAction(self.open_recent_library_menu)
            action.setText(str(path))
            action.triggered.connect(lambda checked=False, p=path: self.open_library_signal.emit(p))
            actions.append(action)

        clear_recent_action = QAction(self.open_recent_library_menu)
        Translations.translate_qobject(clear_recent_action, "menu.file.clear_recent_libraries")
        clear_recent_action.triggered.connect(self._clear_recent_libs)
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
