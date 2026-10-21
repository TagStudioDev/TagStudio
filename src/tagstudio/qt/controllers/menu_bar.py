# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Callable
from pathlib import Path

from PySide6 import QtCore
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMenu, QMenuBar, QWidget

from tagstudio.core.enums import ShowFilepathOption
from tagstudio.i18n.platform_strings import trash_term
from tagstudio.i18n.translations import Translations
from tagstudio.qt.helpers.mnemonics import assign_mnemonics


class MenuBar(QMenuBar):
    file_menu: QMenu
    open_library_action: QAction
    open_recent_library_menu: QMenu
    save_library_backup_action: QAction
    settings_action: QAction
    open_on_start_action: QAction
    sync_library_action: QAction
    close_library_action: QAction

    edit_menu: QMenu
    new_tag_action: QAction
    copy_fields_action: QAction
    paste_fields_action: QAction
    add_tag_to_selected_action: QAction
    delete_file_action: QAction
    ignore_modal_action: QAction
    tag_manager_action: QAction
    field_template_manager_action: QAction
    color_manager_action: QAction

    select_menu: QMenu
    select_all_action: QAction
    clear_select_action: QAction
    select_inverse_action: QAction

    view_menu: QMenu
    library_info_action: QAction
    show_filenames_action: QAction
    increase_thumbnail_size_action: QAction
    decrease_thumbnail_size_action: QAction

    tools_menu: QMenu
    fix_unlinked_entries_action: QAction
    fix_ignored_entries_action: QAction
    fix_dupe_files_action: QAction
    clear_thumb_cache_action: QAction

    macros_menu: QMenu
    folders_to_tags_action: QAction

    help_menu: QMenu
    changelog_action: QAction
    about_action: QAction

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._setup_file_menu()
        self._setup_edit_menu()
        self._setup_select_menu()
        self._setup_view_menu()
        self._setup_tools_menu()
        self._setup_macros_menu()
        self._setup_help_menu()

    def _setup_file_menu(self):
        self.file_menu = QMenu(Translations["menu.file"], self)

        # Open/Create Library
        self.open_library_action = QAction(Translations["menu.file.open_create_library"], self)
        self.open_library_action.setShortcut(QKeySequence("Ctrl+O"))
        self.file_menu.addAction(self.open_library_action)

        # Open Recent
        self.open_recent_library_menu = QMenu(Translations["menu.file.open_recent_library"], self)
        self.file_menu.addMenu(self.open_recent_library_menu)

        # Save Library Backup
        self.save_library_backup_action = QAction(Translations["menu.file.save_backup"], self)
        self.save_library_backup_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.save_library_backup_action.setEnabled(False)
        self.file_menu.addAction(self.save_library_backup_action)

        self.file_menu.addSeparator()

        # Settings
        self.settings_action = QAction(Translations["menu.settings"], self)
        self.file_menu.addAction(self.settings_action)

        # Open Library on Start
        self.open_on_start_action = QAction(Translations["settings.open_library_on_start"], self)
        self.open_on_start_action.setCheckable(True)
        self.file_menu.addAction(self.open_on_start_action)

        self.file_menu.addSeparator()

        # Sync Library
        self.sync_library_action = QAction(Translations["menu.file.sync_library"], self)
        self.sync_library_action.setShortcut(QKeySequence("Ctrl+R"))
        self.sync_library_action.setEnabled(False)
        self.file_menu.addAction(self.sync_library_action)

        self.file_menu.addSeparator()

        # Close Library
        self.close_library_action = QAction(Translations["menu.file.close_library"], self)
        self.close_library_action.setEnabled(False)
        self.file_menu.addAction(self.close_library_action)

        assign_mnemonics(self.file_menu)
        self.addMenu(self.file_menu)

    def _setup_edit_menu(self):
        self.edit_menu = QMenu(Translations["generic.edit_alt"], self)

        # New Tag
        self.new_tag_action = QAction(Translations["menu.edit.new_tag"], self)
        self.new_tag_action.setShortcut(QKeySequence("Ctrl+N"))
        self.new_tag_action.setEnabled(False)
        self.edit_menu.addAction(self.new_tag_action)
        self.edit_menu.addSeparator()

        # Copy Fields
        self.copy_fields_action = QAction(Translations["edit.copy_fields"], self)
        self.copy_fields_action.setShortcut(QKeySequence("Ctrl+C"))
        self.copy_fields_action.setEnabled(False)
        self.edit_menu.addAction(self.copy_fields_action)

        # Paste Fields
        self.paste_fields_action = QAction(Translations["edit.paste_fields"], self)
        self.paste_fields_action.setShortcut(QKeySequence("Ctrl+V"))
        self.paste_fields_action.setEnabled(False)
        self.edit_menu.addAction(self.paste_fields_action)

        # Add Tag to Selected
        self.add_tag_to_selected_action = QAction(Translations["select.add_tag_to_selected"], self)
        self.add_tag_to_selected_action.setShortcut(QKeySequence("Ctrl+Shift+T"))
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

        # Ignore Files and Directories (.ts_ignore System)
        self.ignore_modal_action = QAction(Translations["menu.edit.ignore_files"], self)
        self.ignore_modal_action.setEnabled(False)
        self.edit_menu.addAction(self.ignore_modal_action)

        # Manage Tags
        self.tag_manager_action = QAction(Translations["menu.edit.manage_tags"], self)
        self.tag_manager_action.setShortcut(QKeySequence("Ctrl+M"))
        self.tag_manager_action.setEnabled(False)
        self.edit_menu.addAction(self.tag_manager_action)

        # Color Manager
        self.color_manager_action = QAction(Translations["edit.color_manager"], self)
        self.color_manager_action.setEnabled(False)
        self.edit_menu.addAction(self.color_manager_action)

        # Manage Field Templates
        self.field_template_manager_action = QAction(
            Translations["menu.edit.manage_field_templates"], self
        )
        self.field_template_manager_action.setEnabled(False)
        self.edit_menu.addAction(self.field_template_manager_action)

        assign_mnemonics(self.edit_menu)
        self.addMenu(self.edit_menu)

    def _setup_select_menu(self):
        self.select_menu = QMenu(Translations["menu.select"], self)

        # Select All
        self.select_all_action = QAction(Translations["select.all"], self)
        self.select_all_action.setShortcut(QKeySequence("Ctrl+A"))
        self.select_all_action.setEnabled(False)
        self.select_menu.addAction(self.select_all_action)

        # Clear Selection
        self.clear_select_action = QAction(Translations["select.clear"], self)
        self.clear_select_action.setEnabled(False)
        self.select_menu.addAction(self.clear_select_action)

        # Invert Selection
        self.select_inverse_action = QAction(Translations["select.inverse"], self)
        self.select_inverse_action.setShortcut(QKeySequence("Ctrl+Shift+I"))
        self.select_inverse_action.setEnabled(False)
        self.select_menu.addAction(self.select_inverse_action)

        assign_mnemonics(self.select_menu)
        self.addMenu(self.select_menu)

    def _setup_view_menu(self):
        self.view_menu = QMenu(Translations["menu.view"], self)

        self.library_info_action = QAction(Translations["menu.view.library_info"], self)
        self.library_info_action.setEnabled(False)
        self.view_menu.addAction(self.library_info_action)

        self.show_filenames_action = QAction(Translations["settings.show_filenames_in_grid"], self)
        self.show_filenames_action.setCheckable(True)
        self.view_menu.addAction(self.show_filenames_action)
        self.view_menu.addSeparator()

        self.increase_thumbnail_size_action = QAction(
            Translations["menu.view.increase_thumbnail_size"], self
        )
        self.increase_thumbnail_size_action.setShortcut(QKeySequence("Ctrl++"))
        self.view_menu.addAction(self.increase_thumbnail_size_action)

        self.decrease_thumbnail_size_action = QAction(
            Translations["menu.view.decrease_thumbnail_size"], self
        )
        self.decrease_thumbnail_size_action.setShortcut(QKeySequence("Ctrl+-"))
        self.view_menu.addAction(self.decrease_thumbnail_size_action)

        assign_mnemonics(self.view_menu)
        self.addMenu(self.view_menu)

    def _setup_tools_menu(self):
        self.tools_menu = QMenu(Translations["menu.tools"], self)

        # Fix Unlinked Entries
        self.fix_unlinked_entries_action = QAction(
            Translations["menu.tools.fix_unlinked_entries"], self
        )
        self.fix_unlinked_entries_action.setEnabled(False)
        self.tools_menu.addAction(self.fix_unlinked_entries_action)

        # Fix Ignored Entries
        self.fix_ignored_entries_action = QAction(
            Translations["menu.tools.fix_ignored_entries"], self
        )
        self.fix_ignored_entries_action.setEnabled(False)
        self.tools_menu.addAction(self.fix_ignored_entries_action)

        # Fix Duplicate Files
        self.fix_dupe_files_action = QAction(Translations["menu.tools.fix_duplicate_files"], self)
        self.fix_dupe_files_action.setEnabled(False)
        self.tools_menu.addAction(self.fix_dupe_files_action)

        self.tools_menu.addSeparator()

        # Clear Thumbnail Cache
        self.clear_thumb_cache_action = QAction(
            Translations["settings.clear_thumb_cache.title"], self
        )
        self.clear_thumb_cache_action.setEnabled(False)
        self.tools_menu.addAction(self.clear_thumb_cache_action)

        assign_mnemonics(self.tools_menu)
        self.addMenu(self.tools_menu)

    def _setup_macros_menu(self):
        self.macros_menu = QMenu(Translations["menu.macros"], self)

        self.folders_to_tags_action = QAction(Translations["menu.macros.folders_to_tags"], self)
        self.folders_to_tags_action.setEnabled(False)
        self.macros_menu.addAction(self.folders_to_tags_action)

        assign_mnemonics(self.macros_menu)
        self.addMenu(self.macros_menu)

    def _setup_help_menu(self):
        self.help_menu = QMenu(Translations["menu.help"], self)

        self.about_action = QAction(Translations["menu.help.about"], self)
        self.help_menu.addAction(self.about_action)

        self.changelog_action = QAction(Translations["menu.help.changelog"], self)
        self.help_menu.addAction(self.changelog_action)

        assign_mnemonics(self.help_menu)
        self.addMenu(self.help_menu)

    def set_library_actions_enabled(self, enabled: bool) -> None:
        """Enable or disable the actions that need an open library."""
        for action in (
            self.save_library_backup_action,
            self.close_library_action,
            self.sync_library_action,
            self.tag_manager_action,
            self.color_manager_action,
            self.field_template_manager_action,
            self.ignore_modal_action,
            self.new_tag_action,
            self.fix_unlinked_entries_action,
            self.fix_ignored_entries_action,
            self.fix_dupe_files_action,
            self.clear_thumb_cache_action,
            self.folders_to_tags_action,
            self.library_info_action,
        ):
            action.setEnabled(enabled)

    def rebuild_open_recent_library_menu(
        self,
        libraries: list[Path],
        show_filepath: ShowFilepathOption,
        open_library_callback: Callable[[Path], None],
        clear_libraries_callback: Callable[[], None],
    ):
        menu = self.open_recent_library_menu
        menu.clear()

        for path in libraries:
            text = str(path) if show_filepath == ShowFilepathOption.SHOW_FULL_PATHS else path.name
            action = menu.addAction(text)
            action.triggered.connect(lambda checked=False, p=path: open_library_callback(p))

        if libraries:
            menu.addSeparator()
            clear_recent_action = menu.addAction(Translations["menu.file.clear_recent_libraries"])
            clear_recent_action.triggered.connect(clear_libraries_callback)
        menu.setDisabled(not libraries)
