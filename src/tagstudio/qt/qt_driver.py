# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


# SIGTERM handling based on the implementation by Virgil Dupras for dupeGuru:
# https://github.com/arsenetar/dupeguru/blob/master/run.py#L71


"""A Qt driver for TagStudio."""

import ctypes
import os
import platform
import sys
from argparse import Namespace
from collections.abc import Callable, Iterator
from functools import partial
from pathlib import Path
from queue import Queue
from typing import Any, TypeVar

import semver
import structlog
from humanfriendly import format_size  # pyright: ignore[reportUnknownVariableType]
from PySide6.QtCore import (
    QDeadlineTimer,
    QEvent,
    QObject,
    Qt,
    QThread,
    QThreadPool,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QFontDatabase,
    QGuiApplication,
    QIcon,
    QPalette,
)
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox, QPushButton, QScrollArea

from tagstudio.core.base_driver import BaseDriver
from tagstudio.core.constants import BUILD_TYPE, VERSION
from tagstudio.core.enums import MacroID
from tagstudio.core.library.alchemy.enums import BrowsingState, SortingModeEnum
from tagstudio.core.library.alchemy.library import Library, OpenLibraryResult
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.library.ignore import Ignore
from tagstudio.core.library.library_settings import ShowLabelOption
from tagstudio.core.library.sync import LibrarySyncEngine
from tagstudio.core.utils.ffmpeg_status import FfmpegStatus, FfprobeStatus
from tagstudio.core.utils.module_status import ModuleStatus
from tagstudio.core.utils.ripgrep_status import RipgrepStatus
from tagstudio.core.utils.types import unwrap
from tagstudio.i18n.platform_strings import trash_term
from tagstudio.i18n.translations import Translations
from tagstudio.qt.app_settings import (
    DEFAULT_APP_SETTINGS_PATH,
    AppSettings,
    ShowFilepathOption,
    ThemeOption,
    migrate_legacy_settings,
)
from tagstudio.qt.app_state import DEFAULT_APP_STATE_PATH, AppState, migrate_legacy_cache
from tagstudio.qt.cache_manager import CacheManager
from tagstudio.qt.controllers.about_modal import AboutModal
from tagstudio.qt.controllers.changelog_modal import ChangelogModal
from tagstudio.qt.controllers.edit_tag_panel import EditTagPanel
from tagstudio.qt.controllers.field_template_search_panel import FieldTemplateSearchPanel
from tagstudio.qt.controllers.fix_ignored_entries_modal import FixIgnoredEntriesModal
from tagstudio.qt.controllers.ignore_modal import IgnoreModal
from tagstudio.qt.controllers.library_info_modal import LibraryInfoModal
from tagstudio.qt.controllers.main_window import MainWindow
from tagstudio.qt.controllers.modal import Modal
from tagstudio.qt.controllers.settings_modal import SettingsModal
from tagstudio.qt.controllers.sync_banner import SyncBanner
from tagstudio.qt.controllers.tag_search_panel import TagSearchPanel
from tagstudio.qt.controllers.update_available_message_box import UpdateAvailableMessageBox
from tagstudio.qt.entry_state import EntryState
from tagstudio.qt.mixed.fix_dupe_files import FixDupeFilesModal
from tagstudio.qt.mixed.fix_unlinked import FixUnlinkedEntriesModal
from tagstudio.qt.mixed.folders_to_tags import FoldersToTagsModal
from tagstudio.qt.mixed.migration_modal import JsonMigrationModal
from tagstudio.qt.mixed.tag_color_manager import TagColorManager
from tagstudio.qt.navigator import Navigator
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.selection_state import SelectionState
from tagstudio.qt.utils.custom_runnable import CustomRunnable
from tagstudio.qt.utils.file_deleter import delete_file
from tagstudio.qt.utils.function_iterator import FunctionIterator
from tagstudio.qt.utils.update_check import get_most_recent_release_version, is_version_outdated
from tagstudio.qt.views.search_panel_view import SearchPanelView
from tagstudio.qt.views.styles.image_background import ImageBackground
from tagstudio.qt.views.styles.palette import ColorType, Palette, UiColor, get_ui_color
from tagstudio.qt.views.styles.stylesheets import TagShape, header
from tagstudio.qt.views.styles.tagstudio_style import TagStudioStyle

# SIGQUIT is not defined on Windows
if sys.platform == "win32":
    from signal import SIGINT, SIGTERM, signal

    SIGQUIT = SIGTERM  # pyright: ignore
else:
    from signal import SIGINT, SIGQUIT, SIGTERM, signal  # pyright: ignore

logger = structlog.get_logger(__name__)
T = TypeVar("T")


class Consumer(QThread):
    MARKER_QUIT = "MARKER_QUIT"

    def __init__(self, queue) -> None:
        self.queue = queue
        QThread.__init__(self)

    def run(self):
        while True:
            try:
                job = self.queue.get()
                if job == self.MARKER_QUIT:
                    break
                job[0](*job[1])
            except RuntimeError:
                pass


class QtDriver(BaseDriver, QObject):
    """A Qt GUI frontend driver for TagStudio."""

    SIGTERM = Signal()
    # (Library session ID, library path, open result)
    _open_library_finished = Signal(int, Path, OpenLibraryResult)
    _library_loaded = Signal(int)  # Library session ID

    def __init__(self, args: Namespace):
        super().__init__()
        self.args = args
        self.lib = Library()
        self.cache_manager: CacheManager | None = None
        self.rm: ResourceManager = ResourceManager()

        # State Management
        self.library_pool = QThreadPool(self)
        self.library_pool.setMaxThreadCount(1)
        self._library_session_id = 0
        self._open_library_finished.connect(self._on_open_library_finished)
        self._library_loaded.connect(self._on_library_loaded)
        self.entry_state = EntryState(self.lib, self.library_pool)
        self.selection: SelectionState[int] = SelectionState(lambda: self.navigator.frame_content)
        self.copy_buffer: dict[str, list[Any]] = {"fields": [], "tags": []}

        # Thumbnail Grid
        self.thumb_job_queue: Queue = Queue()
        self.thumb_threads: list[Consumer] = []

        # Sync Engine
        self._sync_session_id: int = 0  # Prevent current sync from affecting subsequent libraries.
        self._sync_pool = QThreadPool(self)
        self._sync_pool.setMaxThreadCount(1)
        self.file_scan_lock: bool = False  # Prevent multiple file scanning operations at once
        self.sync_engine = LibrarySyncEngine(self.lib)

        # Windows
        self.about_modal: Modal | None = None
        self.changelog_modal: Modal | None = None
        self.color_manager: Modal | None = None  # TODO: Convert to full window modes
        self.field_template_manager: Modal | None = None  # TODO: Determine what this folds into
        self.fix_dupe_files_modal: FixDupeFilesModal | None = None
        self.fix_ignored_entries_modal: FixIgnoredEntriesModal | None = None
        self.fix_unlinked_entries_modal: FixUnlinkedEntriesModal | None = None
        self.folders_modal: FoldersToTagsModal | None = None  # NOTE: Deprecated
        self.ignore_files_modal: Modal | None = None
        self.library_info_modal: LibraryInfoModal | None = None
        self.migration_modal: JsonMigrationModal | None = None  # NOTE: Deprecated
        self.new_tag_modal: Modal | None = None
        self.tag_manager: Modal | None = None  # TODO: Convert to full window modes

        self.branch: str = (" (" + Translations[BUILD_TYPE] + ")") if BUILD_TYPE else ""
        self.base_title: str = f"TagStudio Alpha {VERSION}{self.branch}"

        self.SIGTERM.connect(self.handle_sigterm)

        # Load Application Settings File
        app_settings_path = DEFAULT_APP_SETTINGS_PATH
        if self.args.settings_file:
            logger.info(
                "[QtDriver] Using custom application settings path", path=self.args.settings_file
            )
            app_settings_path = Path(self.args.settings_file)
        else:
            logger.info("[QtDriver] Using default application settings path")
            migrate_legacy_settings()
        self.settings = AppSettings.load(app_settings_path)
        if not app_settings_path.exists():
            logger.warning(
                "[QtDriver] Application settings file not found, using defaults",
                path=app_settings_path,
            )
        self.applied_theme = self.settings.theme

        # Load Application State File
        app_state_path = DEFAULT_APP_STATE_PATH
        if self.args.state_file:
            logger.info("[QtDriver] Using custom application state path", path=self.args.state_file)
            app_state_path = Path(self.args.state_file)
        elif self.args.cache_file:
            logger.warning("[QtDriver] -c/--cache-file is deprecated, use --state-file instead")
            legacy_cache_path = Path(self.args.cache_file)
            app_state_path = legacy_cache_path.with_suffix(".json")
            migrate_legacy_cache(legacy_cache_path, app_state_path)
        else:
            logger.info("[QtDriver] Using default application state path")
            migrate_legacy_cache()

        self.app_state = AppState.load(app_state_path)
        if not app_state_path.exists():
            logger.warning(
                "[QtDriver] Application state file not found, using defaults",
                path=app_state_path,
            )

        self.navigator = Navigator(self.lib, self.library_pool, self.selection)
        Translations.change_language(self.settings.language)

    def init_workers(self):
        """Init workers for rendering thumbnails."""
        if not self.thumb_threads:
            max_threads = os.cpu_count() or 1
            for i in range(max_threads):
                thread = Consumer(self.thumb_job_queue)
                thread.setObjectName(f"ThumbRenderer_{i}")
                self.thumb_threads.append(thread)
                thread.start()

    def open_library_from_dialog(self):
        dir = QFileDialog.getExistingDirectory(
            parent=None,
            caption=Translations["window.title.open_create_library"],
            dir=str(Path.home()),
            options=QFileDialog.Option.ShowDirsOnly,
        )
        if dir not in (None, ""):
            self.open_library(Path(dir))

    def signal_handler(self, sig, frame):
        if sig in (SIGINT, SIGTERM, SIGQUIT):
            self.SIGTERM.emit()

    def setup_signals(self):
        signal(SIGINT, self.signal_handler)
        signal(SIGTERM, self.signal_handler)
        signal(SIGQUIT, self.signal_handler)

    def apply_theme(self) -> None:
        """Apply the set theme's color scheme and palette to the app."""
        if self.settings.theme == ThemeOption.DARK:
            self.app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
        elif self.settings.theme == ThemeOption.LIGHT:
            self.app.styleHints().setColorScheme(Qt.ColorScheme.Light)
        else:
            self.app.styleHints().unsetColorScheme()

        self.app.setPalette(QPalette())
        pal: QPalette = self.app.palette()
        # BUG: Changing the palette in any way here seems to affect the accent colors of certain
        # widgets, like QLineEdit focused borders and QComboBox highlighted items and borders.
        # Need to figure out the cause of this.
        if (
            platform.system() == "Darwin" or platform.system() == "Windows"
        ) and QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark:
            pal.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.Window, QColor("#1e1e1e"))
            pal.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.Button, QColor("#1e1e1e"))
            pal.setColor(
                QPalette.ColorGroup.Inactive, QPalette.ColorRole.ToolTipBase, QColor("#1e1e1e")
            )
            pal.setColor(
                QPalette.ColorGroup.Inactive, QPalette.ColorRole.ToolTipText, QColor("#FFFFFF")
            )
            pal.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Window, QColor("#232323"))
            pal.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Button, QColor("#232323"))
            pal.setColor(
                QPalette.ColorGroup.Inactive, QPalette.ColorRole.ButtonText, QColor("#666666")
            )
        # BUG: PySide isn't properly setting the link colors on Windows, so this is a fallback.
        if platform.system() == "Windows":
            pal.setColor(
                QPalette.ColorGroup.Normal,
                QPalette.ColorRole.Link,
                QColor.fromString(get_ui_color(ColorType.PRIMARY, UiColor.BLUE)),
            )
        Palette.set_palette(pal)
        self.app.setPalette(pal)
        for widget in QApplication.allWidgets():
            if widget.styleSheet():
                widget.setStyleSheet(widget.styleSheet())
        theme_change = QEvent(QEvent.Type.ThemeChange)
        for widget in QApplication.allWidgets():
            QApplication.sendEvent(widget, theme_change)
        self.applied_theme = self.settings.theme

    def _on_color_scheme_changed(self) -> None:
        if self.applied_theme == ThemeOption.SYSTEM == self.settings.theme:
            self.apply_theme()

    def start(self) -> None:
        """Launch the main Qt window."""
        if self.settings.theme == ThemeOption.SYSTEM and platform.system() == "Windows":
            sys.argv += ["-platform", "windows:darkmode=2"]
        self.app = QApplication(sys.argv)
        self.app_style = TagStudioStyle()
        self.app.setStyle(self.app_style)

        self.apply_theme()
        self.app.styleHints().colorSchemeChanged.connect(self._on_color_scheme_changed)
        TagShape.is_pill = self.settings.pill_shaped_tags
        TagShape.is_circle_badge = self.settings.circular_badges

        # Handle OS signals
        self.setup_signals()
        # allow to process input from console, eg. SIGTERM
        timer = QTimer()
        timer.start(500)
        timer.timeout.connect(lambda: None)

        # Detect optional modules and versions for logging
        self.log_optional_modules()

        # self.main_window = loader.load(home_path)
        self.main_window = MainWindow(self)
        self.main_window.setWindowTitle(self.base_title)
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()

        if os.name == "nt":
            appid = "cyanvoxel.tagstudio.9"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)

        self.app.setApplicationName("tagstudio")
        self.app.setApplicationDisplayName("TagStudio")
        if platform.system() != "Darwin":
            fallback_icon = QIcon()
            fallback_icon.addFile(str(self.rm.get_path("icon")))
            self.app.setWindowIcon(QIcon.fromTheme("tagstudio", fallback_icon))

            if platform.system() != "Windows":
                self.app.setDesktopFileName("tagstudio")

        tsp_view = SearchPanelView(
            placeholder_text=Translations["home.search_tags"],
            create_text=Translations["tag.create"],
            is_chooser=False,
        )
        tsp = TagSearchPanel(self.lib, is_chooser=False, view=tsp_view)
        tsp.search_for_tag.connect(self.search_for_tag_callback)
        tsp.remove_tag_requested.connect(
            lambda tag_id: self.library_pool.start(partial(self.lib.remove_tag, tag_id))
        )
        self.tag_manager = Modal(tsp, Translations["tag_manager.title"])

        # Initialize the Color Group Manager panel
        self.color_manager = Modal(TagColorManager(self), Translations["color_manager.title"])

        # Initialize the Field Template Manager panel
        self.field_template_manager = Modal(
            content_widget=FieldTemplateSearchPanel(
                self.lib,
                is_chooser=False,
                view=SearchPanelView(
                    Translations["home.search_field_templates"],
                    create_text=Translations["field_template.create"],
                    is_chooser=False,
                ),
            ),
            title=Translations["field_template_manager.title"],
            is_savable=False,
        )
        self.field_template_manager.done.connect(
            lambda checked=False: self.main_window.inspector.update_from_selection(
                update_preview=False
            )
        )

        tag_search = self.main_window.tagging_panel.tag_search
        tag_search.search_for_tag.connect(self.search_for_tag_callback)
        tag_search.item_chosen.connect(
            lambda chosen_tag: self.add_tags_to_selected_callback([chosen_tag])
        )
        self.main_window.inspector.can_add_tags_changed.connect(tag_search.set_capsules_clickable)

        recent_tags = self.main_window.tagging_panel.recent_tags
        recent_tags.search_for_tag.connect(self.search_for_tag_callback)
        recent_tags.tag_chosen.connect(
            lambda chosen_tag: self.entry_state.add_tags(self.selection.selected, chosen_tag)
        )
        self.main_window.inspector.can_add_tags_changed.connect(recent_tags.set_capsules_clickable)

        self.update_recent_lib_menu()

        self.main_window.thumb_grid.visible_changed.connect(
            self.navigator.set_first_visible_entry_id
        )

        QFontDatabase.addApplicationFont(
            str(Path(__file__).parents[1] / "resources/qt/fonts/Oxanium-Bold.ttf")
        )

        show_changelog = self._record_program_version()

        startup_path: str | None = self.args.open.strip() if self.args.open else None
        if not startup_path and self.settings.open_last_loaded_on_startup:
            last_library = self.app_state.last_library
            if last_library:
                startup_path = str(last_library)
        startup_result = None
        if startup_path:
            startup_result = self.verify_library_path(startup_path, allow_creation=False)

        self.init_library_window()

        if startup_result is None:
            self.main_window.browsing_area.landing_page.animate_logo()
        elif startup_result.success and startup_result.library_path:
            self.open_library(startup_result.library_path)
        else:
            self.main_window.browsing_area.landing_page.show_logo()
            self.show_error_message(
                error_name=startup_result.error_title
                or Translations["window.message.error_opening_library"],
                error_desc=startup_result.error_description,
            )

        if show_changelog:
            self.show_changelog()

        self.check_for_update()
        self.app.exec()
        self.shutdown()

    def show_error_message(self, error_name: str, error_desc: str | None = None):
        self.main_window.browsing_area.landing_page.set_status_label(error_name)
        self.main_window.setWindowTitle(f"{self.base_title} - {error_name}")

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setText(error_name)
        if error_desc:
            msg_box.setInformativeText(error_desc)
        msg_box.setWindowTitle(Translations["window.title.error"])
        msg_box.addButton(Translations["generic.close"], QMessageBox.ButtonRole.AcceptRole)

        # Show the message box
        msg_box.exec()

    def init_library_window(self):
        # Browsing and Navigation Signals
        self.main_window.search_bar.search_submitted.connect(self.submit_search)
        self.main_window.set_sorting_mode(self.navigator.browsing_history.current.sorting_mode)
        self.main_window.sorting_mode_changed.connect(self.sorting_mode_callback)
        self.main_window.sorting_direction_changed.connect(self.sorting_direction_callback)
        self.main_window.show_hidden_entries_changed.connect(self.show_hidden_entries_callback)
        self.main_window.navigation_requested.connect(self.navigator.navigation_callback)
        self.main_window.browsing_area.pagination.index.connect(self.navigator.go_to_page)
        self.main_window.pagination_changed.connect(self.set_pagination)
        self.main_window.filenames_visible_changed.connect(self.show_grid_filenames)
        self.main_window.extension_visibility_changed.connect(self.show_grid_extensions)
        self.main_window.duration_visibility_changed.connect(self.show_grid_durations)
        self.main_window.browsing_area.landing_page.open_library_requested.connect(
            self.open_library_from_dialog
        )

    def submit_search(self, query: str) -> None:
        # Clear any banner asking for a manual refresh of the view
        sync_banner = self._sync_banner
        if sync_banner is not None and sync_banner.is_awaiting_refresh:
            sync_banner.hide_banner()
        self.navigator.update_browsing_state(
            BrowsingState.from_search_query(query)
            .with_sorting_mode(self.main_window.sorting_mode)
            .with_sorting_direction(self.main_window.sorting_direction)
            .with_show_hidden_entries(self.main_window.show_hidden_entries),
            searches_again=True,
        )

    def init_ignore_files_modal(self):
        """Initialize the Ignore Files modal."""
        if self.ignore_files_modal:
            self.ignore_files_modal.deleteLater()

        panel = IgnoreModal(self.lib)
        self.ignore_files_modal = Modal(
            panel,
            Translations["menu.edit.ignore_files"],
            is_savable=True,
        )
        self.ignore_files_modal.saved.connect(panel.save)

    def show_grid_filenames(self, value: bool):
        """Save and apply whether the grid shows filenames."""
        self.lib.settings.show_filenames_in_grid = value
        self.lib.settings.save()
        self.main_window.thumb_grid.set_filenames_visible(value)

    def show_grid_extensions(self, option: ShowLabelOption) -> None:
        """Save and apply when the grid shows file extensions."""
        self.lib.settings.show_extensions_in_grid = option
        self.lib.settings.save()
        self.main_window.thumb_grid.update_extension_visibility()

    def show_grid_durations(self, option: ShowLabelOption) -> None:
        """Save and apply when the grid shows durations."""
        self.lib.settings.show_durations_in_grid = option
        self.lib.settings.save()
        self.main_window.thumb_grid.update_duration_visibility()

    def call_if_library_open(self, func):
        """Check if loaded library has valid path before executing the button function."""
        if self.lib.library_dir:
            func()

    def handle_sigterm(self):
        self.shutdown()

    def shutdown(self):
        """Save Library on Application Exit."""
        logger.info("[QtDriver] Shutting down application...")
        self.close_library(is_shutdown=True)

        logger.info("[QtDriver] Ending thumbnail threads...")
        for _ in self.thumb_threads:
            self.thumb_job_queue.put(Consumer.MARKER_QUIT)

        deadline = QDeadlineTimer(1000)
        for thread in self.thumb_threads:
            thread.quit()
            thread.wait(deadline)
        if any(thread.isRunning() for thread in self.thumb_threads):
            logger.warning("[QtDriver] Forcing exit of remaining thumbnail threads...")
            os._exit(0)

        QApplication.quit()

    def close_library(self, is_shutdown: bool = False):
        if not self.lib.library_dir:
            logger.info("[QtDriver] No library to close")
            return
        logger.info("[QtDriver] Closing library...")

        # Invalidate any sync still active for the old library,
        # and wait for the sync to stop before releasing the lock.
        self.sync_engine.cancelled = True
        self._new_sync_session()
        self._wait_for_sync_stop()
        self._set_sync_running(running=False)
        self.main_window.browsing_area.banners.clear()

        if not is_shutdown:
            self.app_state.last_library = None
            self.app_state.save()

        # Reset library state
        self.main_window.search_bar.set_query("")
        self.main_window.tagging_panel.tag_search.set_search_query("")
        self.main_window.tagging_panel.recent_tags.set_tag_ids([])
        self.main_window.set_results_text("")
        scrollbar: QScrollArea = self.main_window.thumb_grid.scroll_area
        scrollbar.verticalScrollBar().setValue(0)
        self.navigator.reset()

        library_settings = self.lib.settings
        if library_settings.thumb_size != self.main_window.thumb_size:
            library_settings.thumb_size = self.main_window.thumb_size
            library_settings.save()

        self._library_session_id += 1
        self.entry_state.wait_for_writes()
        self.lib.close()
        self.sync_engine.reset()
        self.cache_manager = None
        self.thumb_job_queue.queue.clear()

        if is_shutdown:
            return

        self.main_window.setWindowTitle(self.base_title)
        self.selection.clear()
        if self.color_manager:
            self.color_manager.layout().content_widget.reset()

        self.main_window.thumb_grid.set_entries([])
        self.main_window.toggle_landing_page(enabled=True)
        self.main_window.browsing_area.landing_page.animate_logo()
        self.main_window.browsing_area.pagination.setHidden(True)
        self.main_window.menu_bar.set_library_actions_enabled(False)
        self.main_window.search_bar.set_nav_buttons_enabled(False)
        self.main_window.menu_bar.update_select_actions()

    def backup_library(self):
        logger.info("[QtDriver] Backing up library...")
        Library.save_library_backup_to_disk(unwrap(self.lib.library_dir))

    def open_new_tag_modal(self):
        panel = EditTagPanel(self.lib)
        modal = Modal(
            panel,
            Translations["tag.new"],
            Translations["tag.create"],
            is_savable=True,
        )

        modal.saved.connect(
            lambda: (
                self.lib.add_tag(
                    panel.build_tag(),
                    set(panel.parent_ids),
                    set(panel.aliases),
                    set(panel.exclusion_ids),
                ),
                modal.hide(),
            )
        )
        modal.show()
        self.new_tag_modal = modal

    def search_for_tag_callback(self, tag_id: int) -> None:
        """Callback to search for a given Tag ID."""
        self.main_window.search_bar.set_query(f"tag_id:{tag_id}")
        self.navigator.update_browsing_state(
            BrowsingState.from_tag_id(tag_id, self.navigator.browsing_history.current)
        )

    def add_tags_to_selected_callback(self, tag_ids: list[int]):
        self.entry_state.add_tags(self.selection.selected, tag_ids)
        self.main_window.tagging_panel.add_recent_tags(tag_ids)

    def delete_files_callback(self, origin_path: str | Path, origin_id: int | None = None):
        """Callback to send on or more files to the system trash.

        If 0-1 items are currently selected, the origin_path is used to delete the file
        from the originating context menu item.
        If there are currently multiple items selected,
        then the selection buffer is used to determine the files to be deleted.

        Args:
            origin_path(str): The file path associated with the widget making the call.
                May or may not be the file targeted, depending on the selection rules.
            origin_id(id): The entry ID associated with the widget making the call.
        """
        entry: Entry | None = None
        pending: list[tuple[int | None, Path]] = []

        selected = self.selection.selected
        library_dir = unwrap(self.lib.library_dir)

        if len(selected) <= 1 and origin_path:
            origin_id_ = origin_id
            if origin_id_ is None:
                origin_id_ = selected[0] if len(selected) > 0 else None

            pending.append((origin_id_, Path(origin_path)))
        else:
            for item in selected:
                entry = self.lib.get_entry(item)
                if entry is None:
                    continue
                filepath: Path = entry.path
                pending.append((item, filepath))

        if pending and self.delete_file_confirmation(len(pending), pending[0][1]):
            for _, f in pending:
                if (origin_path == f) or (not origin_path):
                    self.main_window.inspector.stop_media_playback()

                delete_file(library_dir / f)

            entry_ids = [e_id for e_id, _ in pending if e_id is not None]
            self.library_pool.start(partial(self.lib.remove_entries, entry_ids))
            self.selection.clear()
            self.navigator.update_browsing_state()

    def delete_file_confirmation(self, count: int, filename: Path | None = None) -> bool:
        """A confirmation dialogue box for deleting files.

        Args:
            count(int): The number of files to be deleted.
            filename(Path | None): The filename to show if only one file is to be deleted.
        """
        # NOTE: Windows + send2trash will PERMANENTLY delete files which cannot be moved to the
        # Recycle Bin. This is done without any warning, so this message is currently the
        # best way I've got to inform the user.
        # https://github.com/arsenetar/send2trash/issues/28
        # This warning is applied to all platforms until at least macOS and Linux can be verified
        # to not exhibit this same behavior.
        perm_warning_msg = Translations.format(
            "trash.dialog.permanent_delete_warning", trash_term=trash_term()
        )
        perm_warning: str = header(
            perm_warning_msg, 4, get_ui_color(ColorType.PRIMARY, UiColor.RED)
        )

        msg = QMessageBox()
        msg.setStyleSheet("font-weight:normal;")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setWindowTitle(
            Translations["trash.dialog.title.singular"]
            if count == 1
            else Translations["trash.dialog.title.plural"]
        )
        msg.setIcon(QMessageBox.Icon.Warning)
        if count <= 1:
            msg_text = Translations.format(
                "trash.dialog.move.confirmation.singular", trash_term=trash_term()
            )
            msg.setText(
                f"{header(msg_text, 3)}"
                f"{header(Translations['trash.dialog.disambiguation_warning.singular'], 4)}"
                f"{filename if filename else ''}"
                f"{perm_warning}<br>"
            )
        elif count > 1:
            msg_text = Translations.format(
                "trash.dialog.move.confirmation.plural",
                count=count,
                trash_term=trash_term(),
            )
            msg.setText(
                f"{header(msg_text, 3)}"
                f"{header(Translations['trash.dialog.disambiguation_warning.plural'], 4)}"
                f"{perm_warning}<br>"
            )

        move_key = (
            "menu.delete_selected_files_singular"
            if count <= 1
            else "menu.delete_selected_files_plural"
        )
        cancel_button = msg.addButton(
            Translations["generic.cancel_alt"], QMessageBox.ButtonRole.RejectRole
        )
        move_button: QPushButton = msg.addButton(
            Translations.format(move_key, trash_term=trash_term()),
            QMessageBox.ButtonRole.AcceptRole,
        )
        msg.setEscapeButton(cancel_button)
        msg.setDefaultButton(cancel_button)

        msg.exec()
        return msg.clickedButton() == move_button

    def _run_sync_step(
        self,
        generator: Callable[[], Iterator[T]],
        on_progress: Callable[[T], None],
        on_done: Callable[[], None],
    ) -> None:
        """Run a generator function on a background thread with signals for progress and completion.

        Args:
            generator (Callable[[], Iterator[T]]): Zero-argument callable returning the
                generator to iterate.
            on_progress (Callable[[T], None]): Called on the main thread with each yielded value.
            on_done (Callable[[], None]): Called on the main thread once `generator` is finished.
        """

        def run_step() -> Iterator[T]:
            """Yield from a generator while catching exceptions to stop sync early."""
            try:
                yield from generator()
            except Exception as e:
                logger.error("[QtDriver] Sync step failed, cancelling sync", error=e)
                self.sync_engine.cancelled = True

        iterator = FunctionIterator(run_step)
        iterator.value.connect(on_progress)
        runnable = CustomRunnable(iterator.run)
        runnable.done.connect(on_done)
        self._sync_pool.start(runnable)

    def _set_sync_running(self, running: bool) -> None:
        self.file_scan_lock = running
        self.main_window.layout().mode_rail.set_sync_running(running)

    def _wait_for_sync_stop(self) -> None:
        """Block until a currently running sync is stopped, if any."""
        self._sync_pool.waitForDone()

    def sync_library_callback(self):
        """Run when syncing a Library is initiated."""
        if self.file_scan_lock:
            logger.info("[QtDriver] Sync already in progress, ignoring request")
            return
        self._set_sync_running(running=True)
        session_id = self._new_sync_session()
        # Disable the "Fix Unlinked Entries" modal's relink/remove actions during the sync
        if self.fix_unlinked_entries_modal and self.fix_unlinked_entries_modal.isVisible():
            self.fix_unlinked_entries_modal.update_unlinked_count()

        engine = self.sync_engine
        library_dir = unwrap(self.lib.library_dir)
        sync_banner = self._create_sync_banner()
        sync_banner.set_preparing()

        def on_progress(progress: tuple[int, int]) -> None:
            sync_banner = self._sync_banner
            if engine.cancelled or self._is_sync_stale(session_id) or sync_banner is None:
                return
            searched_count, found_count = progress
            if searched_count < 0:
                # Scan finished, duplicate entry merging/relinking is running before the next yield
                sync_banner.set_repairing()
                return
            sync_banner.set_scanning(searched_count, found_count)

        def _start_scan() -> None:
            self._run_sync_step(
                lambda lib=library_dir: engine.sync_dir(lib),
                on_progress,
                lambda: self.save_new_entries_runnable(engine, session_id=session_id),
            )

        sync_banner.call_when_open(_start_scan)

    def _finish_sync(
        self,
        new_count: int,
        unlinked_count: int,
        relinked_count: int,
        session_id: int,
    ):
        """Show the sync banner's result notice stage once the sync is completed.

        Args:
            new_count (int): New files count.
            unlinked_count (int): Unlinked entries count.
            relinked_count (int): Automatically relinked files count.
            session_id (int): The sync session this sync started with.
        """
        if self._is_sync_stale(session_id):
            return

        self._set_sync_running(running=False)
        self.lib.unlinked_entries_count = unlinked_count
        if self.fix_unlinked_entries_modal and self.fix_unlinked_entries_modal.isVisible():
            self.fix_unlinked_entries_modal.update_unlinked_count()
            self.fix_unlinked_entries_modal.remove_modal.refresh_list()
        if self.library_info_modal and self.library_info_modal.isVisible():
            self.library_info_modal.update_cleanup()

        if (sync_banner := self._sync_banner) is None:
            return
        if self.sync_engine.cancelled:
            sync_banner.hide_banner(force=True)
        else:
            sync_banner.finish(new_count, unlinked_count, relinked_count)

    @property
    def _sync_banner(self) -> SyncBanner | None:
        """Get the sync banner, if there currently is one."""
        return self.main_window.browsing_area.banners.get(SyncBanner.KEY, SyncBanner)

    def _create_sync_banner(self) -> SyncBanner:
        banner = SyncBanner()
        banner.refresh_requested.connect(self._on_new_files_banner_refresh)
        banner.review_requested.connect(self._on_unlinked_banner_review)
        banner.settings_requested.connect(self._on_sync_disabled_open_settings)
        banner.progress_cancelled.connect(self._on_sync_cancel_requested)
        self.main_window.browsing_area.banners.push(banner, key=SyncBanner.KEY)
        return banner

    def _on_sync_cancel_requested(self) -> None:
        """Stop the current sync at its next opportunity."""
        self.sync_engine.cancelled = True
        logger.info("[QtDriver] Sync cancelled")

    def _new_sync_session(self) -> int:
        """Increment the sync session, invalidating any active sync's callbacks."""
        self._sync_session_id += 1
        return self._sync_session_id

    def _is_sync_stale(self, session_id: int) -> bool:
        """Whether `session_id` belongs to an older sync session and should be invalidated."""
        return session_id != self._sync_session_id

    def _on_new_files_banner_refresh(self):
        self.navigator.update_browsing_state()
        self.main_window.inspector.update_from_selection()
        # If there are still unlinked entries after the automatic relinking step, show a notice.
        sync_banner = self._sync_banner
        if sync_banner is None:
            return
        if self.lib.unlinked_entries_count > 0:
            sync_banner.set_unlinked(self.lib.unlinked_entries_count)
        else:
            sync_banner.hide_banner(force=True)

    def _on_unlinked_banner_review(self):
        if (sync_banner := self._sync_banner) is not None:
            sync_banner.hide_banner(force=True)
        self.open_fix_unlinked_entries_modal()

    def _on_sync_disabled_open_settings(self):
        if (sync_banner := self._sync_banner) is not None:
            sync_banner.hide_banner(force=True)
        SettingsModal.build_modal(self, show_library_settings=True).show()

    def open_library_info_modal(self):
        if not self.library_info_modal:
            self.library_info_modal = LibraryInfoModal(self.lib, self)
        self.library_info_modal.show()

    def open_fix_ignored_entries_modal(self):
        if not self.fix_ignored_entries_modal:
            self.fix_ignored_entries_modal = FixIgnoredEntriesModal(self.lib, self)
        self.fix_ignored_entries_modal.show()

    def open_fix_dupe_files_modal(self):
        if not self.fix_dupe_files_modal:
            self.fix_dupe_files_modal = FixDupeFilesModal(self.lib, self)
        self.fix_dupe_files_modal.show()

    def open_folders_to_tags_modal(self):
        if not self.folders_modal:
            self.folders_modal = FoldersToTagsModal(self.lib, self)
        self.folders_modal.show()

    def open_about_modal(self):
        if not self.about_modal:
            self.about_modal = Modal(
                AboutModal(unwrap(self.settings.path)),
                window_title=Translations["about.title"],
                inline_title=False,
                background=ImageBackground(self.rm.aurora_bg),
            )
        self.about_modal.show()

    def open_fix_unlinked_entries_modal(self):
        if not self.fix_unlinked_entries_modal:
            self.fix_unlinked_entries_modal = FixUnlinkedEntriesModal(self.lib, self)
        self.fix_unlinked_entries_modal.show()

    def sync_entry_stats_runnable(
        self,
        engine: LibrarySyncEngine,
        new_count: int,
        unlinked_count: int,
        relinked_count: int,
        session_id: int,
    ):
        """Start refreshing cached stat() data for files already known to the library."""
        if self._is_sync_stale(session_id):
            return
        restat_count = engine.restat_count

        def on_progress(idx: int) -> None:
            sync_banner = self._sync_banner
            if engine.cancelled or self._is_sync_stale(session_id) or sync_banner is None:
                return
            sync_banner.set_updating(idx, restat_count)

        on_progress(0)
        self._run_sync_step(
            engine.sync_entry_stats,
            on_progress,
            lambda: self._finish_sync(new_count, unlinked_count, relinked_count, session_id),
        )

    def save_new_entries_runnable(self, engine: LibrarySyncEngine, session_id: int):
        """Start adding any known new files to the library."""
        if self._is_sync_stale(session_id):
            return
        new_count = engine.new_file_count
        unlinked_count = -1 if engine.cancelled else engine.unlinked_entries_count
        relinked_count = engine.relinked_entries_count

        def on_progress(idx: int) -> None:
            sync_banner = self._sync_banner
            if engine.cancelled or self._is_sync_stale(session_id) or sync_banner is None:
                return
            sync_banner.set_saving_new_entries(idx, new_count)

        on_progress(0)
        self._run_sync_step(
            engine.save_new_entries,
            on_progress,
            lambda: self.sync_entry_stats_runnable(
                engine, new_count, unlinked_count, relinked_count, session_id
            ),
        )

    def new_file_macros_runnable(self, new_ids):
        """Threaded method that runs macros on a set of Entry IDs."""
        # for i, id in enumerate(new_ids):
        # 	# pb.setValue(i)
        # 	# pb.setLabelText(f'Running Configured Macros on {i}/{len(new_ids)} New Entries')
        # 	# self.run_macro('autofill', id)
        yield 0

    def run_macros(self, name: MacroID, entry_ids: list[int]):
        """Run a specific Macro on a group of given entry_ids."""
        for entry_id in entry_ids:
            self.run_macro(name, entry_id)

    def run_macro(self, name: MacroID, entry_id: int):
        """Run a specific Macro on an Entry given a Macro name."""
        entry: Entry = unwrap(self.lib.get_entry(entry_id))
        source = "" if entry.path.parent == Path(".") else entry.path.parts[0].lower()

        logger.info(
            "running macro",
            source=source,
            macro=name,
            entry_id=entry.id,
            grid_idx=entry_id,
        )

        if name == MacroID.AUTOFILL:
            for macro_id in MacroID:
                if macro_id == MacroID.AUTOFILL:
                    continue
                self.run_macro(macro_id, entry_id)

    def sorting_direction_callback(self, ascending: bool):
        logger.info("[QtDriver] Sorting Direction Changed", ascending=ascending)
        self.navigator.update_browsing_state(
            self.navigator.browsing_history.current.with_sorting_direction(ascending)
        )

    def sorting_mode_callback(self, mode: SortingModeEnum):
        logger.info("[QtDriver] Sorting Mode Changed", mode=mode)
        self.navigator.update_browsing_state(
            self.navigator.browsing_history.current.with_sorting_mode(mode)
        )

    def show_hidden_entries_callback(self, show_hidden_entries: bool):
        logger.info("[QtDriver] Show Hidden Entries Changed", exclude=show_hidden_entries)
        self.navigator.update_browsing_state(
            self.navigator.browsing_history.current.with_show_hidden_entries(show_hidden_entries)
        )

    def set_pagination(self, is_infinite: bool, page_size: int) -> None:
        """Save and apply pagination settings."""
        self.lib.settings.infinite_scroll = is_infinite
        self.lib.settings.page_size = page_size
        self.lib.settings.save()
        current = self.navigator.browsing_history.current
        self.navigator.update_browsing_state(
            current.with_page_index(0) if current.page_index else None
        )

    def copy_fields_action_callback(self):
        if len(self.selection.selected) > 0:
            entry = self.lib.get_entry_full(self.selection.selected[0])
            if entry:
                self.copy_buffer["fields"] = entry.fields
                self.copy_buffer["tags"] = list(
                    self.entry_state.tag_ids_with_pending_writes(
                        entry.id, {tag.id for tag in entry.tags}
                    )
                )
        self.main_window.menu_bar.update_clipboard_actions()

    def paste_fields_action_callback(self):
        for id in self.selection.selected:
            entry = self.lib.get_entry_full(id, with_fields=True, with_tags=False)
            if not entry:
                continue
            existing_fields = entry.fields
            for field in self.copy_buffer["fields"]:
                exists = False
                for e in existing_fields:
                    if field == e:
                        exists = True
                if not exists:
                    self.lib.add_field_to_entries(id, field=field)
        if self.copy_buffer["tags"]:
            self.entry_state.add_tags(self.selection.selected, self.copy_buffer["tags"])
        elif len(self.selection.selected) == 1:
            self.main_window.inspector.containers.update_from_entry(self.selection.selected[0])

    def update_recent_lib_menu(self):
        """Update the recent library menu."""
        self.main_window.menu_bar.rebuild_open_recent_library_menu(
            self.app_state.recent_libraries,
            self.settings.show_filepath,  # TODO: once QtDriver is a Singleton remove this parameter
            self.open_library,
            self.clear_recent_libs,
        )

    def clear_recent_libs(self):
        """Clear the list of recent libraries."""
        self.app_state.recent_libraries = []
        self.app_state.save()
        self.update_recent_lib_menu()

    def open_settings_modal(self):
        SettingsModal.build_modal(self).show()

    def check_for_update(self):
        """Check for an update to TagStudio and display a notification if there is one."""

        def fetch_latest_version() -> None:
            get_most_recent_release_version()

        runnable = CustomRunnable(fetch_latest_version)
        runnable.done.connect(self._show_available_update)
        QThreadPool.globalInstance().start(runnable)

    def _show_available_update(self) -> None:
        latest_version = get_most_recent_release_version()
        if latest_version == self.app_state.dismissed_update:
            return

        if latest_version and is_version_outdated(VERSION, latest_version):
            update_box = UpdateAvailableMessageBox()
            update_box.button(QMessageBox.StandardButton.Ignore).clicked.connect(
                partial(self.dismiss_update, str(latest_version))
            )
            update_box.exec()

    def _record_program_version(self) -> bool:
        """Record the version of the program to the application state file.

        Returns:
            bool: True if the current version is newer than the previously recorded one.
                Will be False on first time runs of the program, and True if it's not the first run
                but there's no existing record of the last version used.
        """
        is_first_run = self.app_state.model_dump() == AppState().model_dump()
        last_version_opened = self.app_state.last_version_opened
        self.app_state.last_version_opened = VERSION
        self.app_state.save()

        if is_first_run:
            return False
        if not last_version_opened:
            return True
        try:
            return semver.Version.parse(str(last_version_opened)) < semver.Version.parse(VERSION)
        except ValueError:
            return str(last_version_opened) != VERSION

    def show_changelog(self):
        if not self.changelog_modal:
            self.changelog_modal = Modal(
                ChangelogModal(),
                window_title=Translations["changelog.window_title"],
                inline_title=False,
                background=ImageBackground(self.rm.aurora_bg),
            )
        self.changelog_modal.show()

    def dismiss_update(self, version: str):
        """Dismiss an update notification for a specific new version of TagStudio."""
        self.app_state.dismissed_update = version
        self.app_state.save()

    def open_library(self, path: Path) -> None:
        """Open a TagStudio library."""
        library_dir_display = (
            path if self.settings.show_filepath == ShowFilepathOption.SHOW_FULL_PATHS else path.name
        )
        if self.lib.library_dir:
            self.close_library()
        self._library_session_id += 1  # Ignore results of earlier open_library calls
        session_id = self._library_session_id

        message = Translations.format("splash.opening_library", library_path=library_dir_display)
        self.main_window.browsing_area.landing_page.set_status_label(message)
        self.main_window.browsing_area.landing_page.show_logo()

        if Library.needs_migration(path):
            message = Translations.format(
                "splash.migrating_library", library_path=library_dir_display
            )
            self.main_window.browsing_area.landing_page.set_status_label(message)

        def _open() -> None:
            """Open the library on the library thread pool."""
            if self.lib.library_dir:  # Left open by an earlier open_library call
                self.lib.close()
            open_status: OpenLibraryResult | None = None
            try:
                open_status = self.lib.open_library(path)
            except ValueError as e:
                logger.warning(e)
                open_status = OpenLibraryResult(
                    success=False,
                    library_path=path,
                    error_title=Translations["menu.file.missing_library.title"],
                    error_description=Translations.format(
                        "menu.file.missing_library.message", library=library_dir_display
                    ),
                )
            except Exception as e:
                logger.error("[QtDriver] Couldn't open library", error=e)
                open_status = OpenLibraryResult(
                    success=False, library_path=path, error_description=f"{type(e).__name__}: {e}"
                )
            self._open_library_finished.emit(session_id, path, open_status)

        self.library_pool.start(_open)

    def _on_open_library_finished(
        self, session_id: int, path: Path, open_status: OpenLibraryResult
    ) -> None:
        if session_id != self._library_session_id:
            return
        self.cache_manager = CacheManager(
            path,
            max_size=self.lib.settings.thumb_cache_size,
            img_quality=self.lib.settings.cached_thumb_quality,
        )
        cache_size = self.lib.settings.thumb_cache_size * self.cache_manager.STAT_MULTIPLIER
        logger.info(
            f"[Config] Thumbnail Cache Size: {format_size(cache_size)}",
        )

        # Migration is required
        if open_status.needs_json_migration:
            self.migration_modal = JsonMigrationModal(path)
            self.migration_modal.migration_finished.connect(
                lambda: self._init_library(path, self.lib.open_library(path))
            )
            self.main_window.browsing_area.landing_page.set_status_label("")
            self.main_window.toggle_landing_page(enabled=True)
            self.migration_modal.paged_panel.show()
        else:
            self._init_library(path, open_status)

    def _init_library(self, path: Path, open_status: OpenLibraryResult):
        if not open_status.success:
            self.main_window.toggle_landing_page(enabled=True)
            self.show_error_message(
                error_name=open_status.error_title
                or Translations["window.message.error_opening_library"],
                error_desc=open_status.error_description,
            )
            return open_status

        assert self.lib.library_dir
        self.init_workers()
        Ignore.get_patterns(self.lib.library_dir, include_global=True)
        # Start the history at the current sort, so back doesn't lead to the default one
        initial_state = BrowsingState(
            page_index=0,
            sorting_mode=self.main_window.sorting_mode,
            ascending=self.main_window.sorting_direction,
        )
        self.navigator.reset(initial_state)

        library_settings = self.lib.settings
        self.main_window.set_thumb_size(library_settings.thumb_size)
        self.main_window.set_pagination_actions_checked(
            library_settings.infinite_scroll, library_settings.page_size
        )
        self.main_window.set_show_filenames_action_checked(library_settings.show_filenames_in_grid)
        self.main_window.thumb_grid.set_filenames_visible(library_settings.show_filenames_in_grid)
        self.main_window.set_show_extensions_action_checked(
            library_settings.show_extensions_in_grid
        )
        self.main_window.set_show_durations_action_checked(library_settings.show_durations_in_grid)

        if not self.lib.settings.sync_on_open:
            # Show that the setting for syncing a library on open is turned off,
            # with a prompt to open the settings to change that (encouraged but not required).
            self._create_sync_banner().set_disabled_notice()

        if self.settings.show_filepath == ShowFilepathOption.SHOW_FULL_PATHS:
            library_dir_display = self.lib.library_dir
        else:
            library_dir_display = self.lib.library_dir.name

        self.app_state.add_recent_library(path)
        self.app_state.last_library = path
        self.app_state.save()
        self.update_recent_lib_menu()
        self.main_window.setWindowTitle(
            Translations.format(
                "app.title",
                base_title=self.base_title,
                library_dir=library_dir_display,
            )
        )
        self.main_window.setAcceptDrops(True)
        self.init_ignore_files_modal()
        self.main_window.menu_bar.set_library_actions_enabled(True)
        self.main_window.inspector.update_from_selection()
        self.navigator.update_browsing_state()
        self.library_pool.start(partial(self._library_loaded.emit, self._library_session_id))

        return open_status

    def _on_library_loaded(self, session_id: int) -> None:
        if session_id != self._library_session_id:
            return
        # Leave the landing page once the opened library's first results have loaded
        self.main_window.toggle_landing_page(enabled=False)
        self.main_window.thumb_grid.scroll_area.setFocus()
        if self.lib.settings.sync_on_open:
            self.sync_library_callback()

    def log_optional_modules(self) -> None:
        """Logs the status of optional modules."""
        status_classes: list[tuple[str, type[ModuleStatus]]] = [
            ("FFmpeg", FfmpegStatus),
            ("FFprobe", FfprobeStatus),
            ("ripgrep", RipgrepStatus),
        ]

        for name, sc in status_classes:
            if sc.which():
                logger.info(f"[QtDriver] {name} found", which=sc.which(), version=sc.version())
            else:
                logger.warning(f"[QtDriver] {name} not found")
