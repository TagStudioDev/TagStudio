# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


# SIGTERM handling based on the implementation by Virgil Dupras for dupeGuru:
# https://github.com/arsenetar/dupeguru/blob/master/run.py#L71


"""A Qt driver for TagStudio."""

import ctypes
import math
import os
import platform
import sys
import time
from argparse import Namespace
from collections.abc import Callable, Iterator
from functools import partial
from pathlib import Path
from queue import Queue
from typing import TypeVar
from warnings import catch_warnings

import semver
import structlog
from humanfriendly import format_size, format_timespan  # pyright: ignore[reportUnknownVariableType]
from PySide6.QtCore import (
    QDeadlineTimer,
    QObject,
    QSettings,
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

from tagstudio.core.constants import BUILD_TYPE, VERSION
from tagstudio.core.driver import DriverMixin
from tagstudio.core.enums import AppCacheItems, MacroID, ShowFilepathOption
from tagstudio.core.library.alchemy.enums import BrowsingState, SortingModeEnum
from tagstudio.core.library.alchemy.library import Library, OpenLibraryResult
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.library.ignore import Ignore
from tagstudio.core.library.sync import LibrarySyncEngine
from tagstudio.core.query_lang.util import ParsingError
from tagstudio.core.ts_core import TagStudioCore
from tagstudio.core.utils.ffmpeg_status import FfmpegStatus, FfprobeStatus
from tagstudio.core.utils.module_status import ModuleStatus
from tagstudio.core.utils.ripgrep_status import RipgrepStatus
from tagstudio.core.utils.str_formatting import is_version_outdated
from tagstudio.core.utils.types import unwrap
from tagstudio.i18n.platform_strings import trash_term
from tagstudio.i18n.translations import Translations
from tagstudio.qt.app_settings import DEFAULT_GLOBAL_SETTINGS_PATH, AppSettings, Theme
from tagstudio.qt.cache_manager import CacheManager
from tagstudio.qt.controllers.changelog_modal import ChangelogModal
from tagstudio.qt.controllers.edit_tag_panel import EditTagPanel
from tagstudio.qt.controllers.field_template_search_panel import FieldTemplateSearchPanel
from tagstudio.qt.controllers.fix_ignored_modal import FixIgnoredEntriesModal
from tagstudio.qt.controllers.ignore_modal import IgnoreModal
from tagstudio.qt.controllers.library_info_window import LibraryInfoWindow
from tagstudio.qt.controllers.main_window import MainWindow
from tagstudio.qt.controllers.modal import Modal
from tagstudio.qt.controllers.splash import SplashScreen
from tagstudio.qt.controllers.sync_banner import SyncBanner
from tagstudio.qt.controllers.tag_search_panel import TagSearchPanel
from tagstudio.qt.controllers.update_available_message_box import UpdateAvailableMessageBox
from tagstudio.qt.entry_state import EntryState
from tagstudio.qt.mixed.about_modal import AboutModal
from tagstudio.qt.mixed.fix_dupe_files import FixDupeFilesModal
from tagstudio.qt.mixed.fix_unlinked import FixUnlinkedEntriesModal
from tagstudio.qt.mixed.folders_to_tags import FoldersToTagsModal
from tagstudio.qt.mixed.migration_modal import JsonMigrationModal
from tagstudio.qt.mixed.settings_panel import SettingsPanel
from tagstudio.qt.mixed.tag_color_manager import TagColorManager
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.selection_state import SelectionState
from tagstudio.qt.utils.custom_runnable import CustomRunnable
from tagstudio.qt.utils.file_deleter import delete_file
from tagstudio.qt.utils.function_iterator import FunctionIterator
from tagstudio.qt.views.search_panel_view import SearchPanelView
from tagstudio.qt.views.styles.palette import ColorType, Palette, UiColor, get_ui_color
from tagstudio.qt.views.styles.stylesheets import header

# SIGQUIT is not defined on Windows
if sys.platform == "win32":
    from signal import SIGINT, SIGTERM, signal

    SIGQUIT = SIGTERM  # pyright: ignore
else:
    from signal import SIGINT, SIGQUIT, SIGTERM, signal  # pyright: ignore

logger = structlog.get_logger(__name__)
T = TypeVar("T")


def clamp(value, lower_bound, upper_bound):
    return max(lower_bound, min(upper_bound, value))


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


# Ex. User visits | A ->[B]     |
#                 | A    B ->[C]|
#                 | A   [B]<- C |
#                 |[A]<- B    C |  Previous routes still exist
#                 | A ->[D]     |  Stack is cut from [:A] on new route
class History[T]:
    __history: list[T]
    __index: int = 0

    def __init__(self, initial_value: T):
        self.__history = [initial_value]
        super().__init__()

    def erase_future(self) -> None:
        self.__history = self.__history[: self.__index + 1]

    def push(self, value: T) -> None:
        """Make `value` current and drop any forward history, unless it equals the current one."""
        if value == self.current:
            return
        self.erase_future()
        self.__history.append(value)
        self.__index = len(self.__history) - 1

    def move(self, delta: int) -> bool:
        """Move through the history, returning whether the current value changed."""
        index = clamp(self.__index + delta, 0, len(self.__history) - 1)
        moved = index != self.__index
        self.__index = index
        return moved

    @property
    def current(self) -> T:
        return self.__history[self.__index]


class QtDriver(DriverMixin, QObject):
    """A Qt GUI frontend driver for TagStudio."""

    SIGTERM = Signal()

    tag_manager: Modal | None = None
    color_manager_panel: TagColorManager | None = None
    field_template_manager: Modal | None = None
    ignore_modal: Modal | None = None
    add_tag_modal: Modal | None = None
    add_field_modal: Modal | None = None
    folders_modal: FoldersToTagsModal
    about_modal: AboutModal
    unlinked_modal: FixUnlinkedEntriesModal
    ignored_modal: FixIgnoredEntriesModal
    dupe_modal: FixDupeFilesModal
    library_info_window: LibraryInfoWindow

    applied_theme: Theme

    lib: Library
    cache_manager: CacheManager | None = None

    browsing_history: History[BrowsingState]

    def __init__(self, args: Namespace):
        super().__init__()
        self.args = args
        self.lib = Library()
        self.rm: ResourceManager = ResourceManager()

        # State Management
        self.entry_state = EntryState(self.lib)
        self.selection: SelectionState[int] = SelectionState(lambda: self.frame_content)
        self.selection.changed.connect(self._on_selection_changed)

        # Thumbnail Grid
        self.frame_content: list[int] = []  # List of Entry IDs for the current query
        self._results_state: BrowsingState | None = None
        self.thumb_job_queue: Queue = Queue()
        self.thumb_threads: list[Consumer] = []

        # Sync Engine
        self._sync_disabled_notice_shown: bool = False
        self._sync_session_id: int = 0  # Prevent current sync from affecting subsequent libraries.
        self._sync_pool = QThreadPool(self)
        self._sync_pool.setMaxThreadCount(1)
        self.file_scan_lock: bool = False  # Prevent multiple file scanning operations at once
        self.pages_count = 0
        self.sync_engine = LibrarySyncEngine(self.lib)

        self.branch: str = (" (" + Translations[BUILD_TYPE] + ")") if BUILD_TYPE else ""
        self.base_title: str = f"TagStudio Alpha {VERSION}{self.branch}"

        self.SIGTERM.connect(self.handle_sigterm)

        self.global_settings_path = DEFAULT_GLOBAL_SETTINGS_PATH
        if self.args.settings_file:
            self.global_settings_path = Path(self.args.settings_file)
        else:
            logger.info("[Settings] Global Settings File Path not specified, using default")
        self.settings = AppSettings.read_settings(self.global_settings_path)
        if not self.global_settings_path.exists():
            logger.warning(
                "[Settings] Global Settings File does not exist creating",
                path=self.global_settings_path,
            )
        self.applied_theme = self.settings.theme

        self.__reset_navigation()

        if self.args.cache_file:
            path = Path(self.args.cache_file)
            if not path.exists():
                logger.warning("[Cache] Cache File does not exist creating", path=path)
            logger.info("[Cache] Using Cache File", path=path)
            self.cached_values = QSettings(str(path), QSettings.Format.IniFormat)
        else:
            self.cached_values = QSettings(
                QSettings.Format.IniFormat,
                QSettings.Scope.UserScope,
                "TagStudio",
                "TagStudio",
            )
            logger.info(
                "[Cache] Cache File not specified, using default one",
                filename=self.cached_values.fileName(),
            )

        Translations.change_language(self.settings.language)

    def __reset_navigation(self) -> None:
        self.browsing_history = History(BrowsingState.show_all())

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

    def start(self) -> None:
        """Launch the main Qt window."""
        if self.settings.theme == Theme.SYSTEM and platform.system() == "Windows":
            sys.argv += ["-platform", "windows:darkmode=2"]
        self.app = QApplication(sys.argv)
        self.app.setStyle("Fusion")

        # Apply theme color if explicitly set to DARK or LIGHT by the user.
        # For SYSTEM, we let Qt decide based on OS theme.
        if self.settings.theme == Theme.DARK:
            self.app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
        elif self.settings.theme == Theme.LIGHT:
            self.app.styleHints().setColorScheme(Qt.ColorScheme.Light)

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

        self.splash: SplashScreen = SplashScreen(
            resource_manager=self.rm,
            screen_width=QGuiApplication.primaryScreen().geometry().width(),
            splash_name=self.settings.splash,
            device_ratio=self.main_window.devicePixelRatio(),
        )
        self.splash.show()

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
        self.tag_manager = Modal(tsp, Translations["tag_manager.title"])
        self.tag_manager.done.connect(
            lambda checked=False: self.main_window.inspector.update_from_selection(
                update_preview=False
            )
        )

        # Initialize the Color Group Manager panel
        self.color_manager_panel = TagColorManager(self)

        # Initialize the Field Template Manager panel
        self.field_template_manager = Modal(
            content_widget=FieldTemplateSearchPanel(
                self.lib,
                is_chooser=False,
                view=SearchPanelView(Translations["home.search_field_templates"], is_chooser=False),
            ),
            title=Translations["field_template_manager.title"],
            is_savable=False,
        )
        self.field_template_manager.done.connect(
            lambda checked=False: self.main_window.inspector.update_from_selection(
                update_preview=False
            )
        )

        # TODO: Remove/replace this with a suite of persistently visible tagging panels, including
        # tag search. These will be docked on the left-hand side of the main window.

        # Initialize the "Add Tag" panel
        add_tag_tsp_view = SearchPanelView(placeholder_text=Translations["home.search_tags"])
        add_tag_tsp = TagSearchPanel(self.lib, view=add_tag_tsp_view)
        add_tag_tsp.search_for_tag.connect(self.search_for_tag_callback)
        self.add_tag_modal = Modal(add_tag_tsp, Translations["tag.add.plural"])
        add_tag_tsp.item_chosen.connect(
            lambda chosen_tag: self.add_tags_to_selected_callback([chosen_tag])
        )

        # region Menu Bar

        # region File Menu ============================================================
        # Open/Create Library
        self.main_window.menu_bar.open_library_action.triggered.connect(
            self.open_library_from_dialog
        )

        # Open Recent
        self.update_recent_lib_menu()

        # Save Library Backup
        self.main_window.menu_bar.save_library_backup_action.triggered.connect(
            lambda: self.call_if_library_open(self.backup_library)
        )

        # Settings
        self.main_window.menu_bar.settings_action.triggered.connect(self.open_settings_modal)

        # Reopen Library on Start
        self.main_window.menu_bar.open_on_start_action.setChecked(
            self.settings.open_last_loaded_on_startup
        )

        def set_open_last_loaded_on_startup(checked: bool):
            self.settings.open_last_loaded_on_startup = checked
            self.settings.save()

        self.main_window.menu_bar.open_on_start_action.triggered.connect(
            set_open_last_loaded_on_startup
        )

        # Sync Library
        self.main_window.menu_bar.sync_library_action.triggered.connect(
            lambda: self.call_if_library_open(self.sync_library_callback)
        )

        # Close Library
        self.main_window.menu_bar.close_library_action.triggered.connect(self.close_library)

        # endregion

        # region Edit Menu ============================================================
        self.main_window.menu_bar.new_tag_action.triggered.connect(
            lambda: self.add_tag_action_callback()
        )

        self.main_window.menu_bar.select_all_action.triggered.connect(self.selection.select_all)

        self.main_window.menu_bar.select_inverse_action.triggered.connect(
            self.selection.select_inverse
        )

        self.main_window.menu_bar.clear_select_action.triggered.connect(self.selection.clear)

        self.copy_buffer: dict = {"fields": [], "tags": []}

        self.main_window.menu_bar.copy_fields_action.triggered.connect(
            self.copy_fields_action_callback
        )

        self.main_window.menu_bar.paste_fields_action.triggered.connect(
            self.paste_fields_action_callback
        )

        self.main_window.menu_bar.add_tag_to_selected_action.triggered.connect(
            self.add_tag_modal.show
        )

        self.main_window.menu_bar.delete_file_action.triggered.connect(
            lambda f="": self.delete_files_callback(f)
        )

        self.main_window.menu_bar.tag_manager_action.triggered.connect(self.tag_manager.show)

        self.main_window.menu_bar.color_manager_action.triggered.connect(
            self.color_manager_panel.show
        )

        self.main_window.menu_bar.field_template_manager_action.triggered.connect(
            self.field_template_manager.show
        )

        # endregion

        # region View Menu ============================================================

        def create_library_info_window():
            if not hasattr(self, "library_info_window"):
                self.library_info_window = LibraryInfoWindow(self.lib, self)
            self.library_info_window.show()

        self.main_window.menu_bar.library_info_action.triggered.connect(create_library_info_window)

        def on_show_filenames_action(checked: bool):
            self.settings.show_filenames_in_grid = checked
            self.settings.save()
            self.show_grid_filenames(checked)

        self.main_window.menu_bar.show_filenames_action.triggered.connect(on_show_filenames_action)
        self.main_window.menu_bar.show_filenames_action.setChecked(
            self.settings.show_filenames_in_grid
        )

        self.main_window.menu_bar.decrease_thumbnail_size_action.triggered.connect(
            self.main_window.decrease_thumb_size
        )
        self.main_window.menu_bar.increase_thumbnail_size_action.triggered.connect(
            self.main_window.increase_thumb_size
        )

        # endregion

        # region Tools Menu ===========================================================

        self.main_window.menu_bar.fix_unlinked_entries_action.triggered.connect(
            self.open_fix_unlinked_entries_modal
        )

        def create_ignored_entries_modal():
            if not hasattr(self, "ignored_modal"):
                self.ignored_modal = FixIgnoredEntriesModal(self.lib, self)
            self.ignored_modal.show()

        self.main_window.menu_bar.fix_ignored_entries_action.triggered.connect(
            create_ignored_entries_modal
        )

        def create_dupe_files_modal():
            if not hasattr(self, "dupe_modal"):
                self.dupe_modal = FixDupeFilesModal(self.lib, self)
            self.dupe_modal.show()

        self.main_window.menu_bar.fix_dupe_files_action.triggered.connect(create_dupe_files_modal)

        # TODO: Make this accessible somewhere more sensible too, like "Library Information"
        self.main_window.menu_bar.clear_thumb_cache_action.triggered.connect(
            lambda: unwrap(self.cache_manager).clear_cache()
        )

        # endregion

        # region Macros Menu ==========================================================
        def create_folders_tags_modal():
            if not hasattr(self, "folders_modal"):
                self.folders_modal = FoldersToTagsModal(self.lib, self)
            self.folders_modal.show()

        self.main_window.menu_bar.folders_to_tags_action.triggered.connect(
            create_folders_tags_modal
        )

        # endregion

        # region Help Menu ============================================================
        def create_about_modal():
            if not hasattr(self, "about_modal"):
                self.about_modal = AboutModal(self.global_settings_path)
            self.about_modal.show()

        self.main_window.menu_bar.about_action.triggered.connect(create_about_modal)
        self.main_window.menu_bar.changelog_action.triggered.connect(self.show_changelog)

        # endregion

        # endregion

        def on_visible_changed(entry_id: int):
            self.browsing_history.current.first_visible_entry_id = entry_id

        self.main_window.thumb_grid.visible_changed.connect(on_visible_changed)

        QFontDatabase.addApplicationFont(
            str(Path(__file__).parents[1] / "resources/qt/fonts/Oxanium-Bold.ttf")
        )

        show_changelog = self._record_program_version()
        self.init_library_window()
        self.migration_modal: JsonMigrationModal | None = None

        startup_path: str | None = self.args.open.strip() if self.args.open else None
        if not startup_path and self.settings.open_last_loaded_on_startup:
            last_library = self.cached_values.value(AppCacheItems.LAST_LIBRARY)
            if last_library:
                startup_path = str(last_library)

        if not startup_path:
            self.main_window.browsing_area.landing_widget.animate_logo_in()
        else:
            startup_result = self.verify_library_path(startup_path, allow_creation=False)
            if startup_result.success and startup_result.library_path:
                self.open_library(startup_result.library_path)
            else:
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
        self.main_window.browsing_area.landing_widget.set_status_label(error_name)
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
        # self._init_landing_page() # Taken care of inside the widget now

        # TODO: Put this into its own method that copies the font file(s) into memory
        # so the resource isn't being used, then store the specific size variations
        # in a global dict for methods to access for different DPIs.
        # adj_font_size = math.floor(12 * self.main_window.devicePixelRatio())

        # Search Button and Field
        self.main_window.search_bar.search_submitted.connect(self.submit_search)

        # Sorting Dropdowns
        self.main_window.set_sorting_mode(self.browsing_history.current.sorting_mode)
        self.main_window.sorting_mode_changed.connect(self.sorting_mode_callback)
        self.main_window.sorting_direction_changed.connect(self.sorting_direction_callback)

        # Exclude hidden entries checkbox
        self.main_window.show_hidden_entries_changed.connect(self.show_hidden_entries_callback)

        self.main_window.navigation_requested.connect(self.navigation_callback)

        # NOTE: Putting this too early will result in a non-responsive white window on start.
        self.main_window.show()
        self.main_window.activateWindow()
        self.main_window.browsing_area.toggle_landing_page(enabled=True)

        self.main_window.browsing_area.pagination.index.connect(
            lambda i: self.page_move(i, absolute=True)
        )

        self.splash.finish(self.main_window)

    def submit_search(self, query: str) -> None:
        # Clear any banner asking for a manual refresh of the view
        sync_banner = self._sync_banner
        if sync_banner is not None and sync_banner.is_awaiting_refresh:
            sync_banner.hide_banner()
        self._results_state = None  # Submitting a search always searches again
        try:
            self.update_browsing_state(
                BrowsingState.from_search_query(query)
                .with_sorting_mode(self.main_window.sorting_mode)
                .with_sorting_direction(self.main_window.sorting_direction)
                .with_show_hidden_entries(self.main_window.show_hidden_entries)
            )
        except ParsingError as e:
            self.main_window.set_results_text(
                f'{Translations["status.results.invalid_syntax"]} "{query}"'
            )
            logger.error("[QtDriver] Could not update BrowsingState", error=e)

    def init_ignore_modal(self):
        """Initialize the Ignore Files panel."""
        if self.ignore_modal:
            with catch_warnings(record=True):
                self.main_window.menu_bar.ignore_modal_action.triggered.disconnect()
                self.ignore_modal.saved.disconnect()
            self.ignore_modal.deleteLater()
            self.ignore_modal = None

        panel = IgnoreModal(self.lib)
        self.ignore_modal = Modal(
            panel,
            Translations["menu.edit.ignore_files"],
            is_savable=True,
        )
        self.ignore_modal.saved.connect(panel.save)
        self.main_window.menu_bar.ignore_modal_action.triggered.connect(self.ignore_modal.show)

    def show_grid_filenames(self, value: bool):
        self.main_window.thumb_grid.set_filenames_visible(value)

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
        self.file_scan_lock = False
        self.main_window.browsing_area.banners.clear()

        if not is_shutdown:
            self.cached_values.remove(AppCacheItems.LAST_LIBRARY)
            self.cached_values.sync()

        # Reset library state
        self.main_window.search_bar.set_query("")
        self.main_window.set_results_text("")
        scrollbar: QScrollArea = self.main_window.thumb_grid.scroll_area
        scrollbar.verticalScrollBar().setValue(0)
        self.__reset_navigation()

        self.lib.close()
        self.sync_engine.reset()
        self.cache_manager = None
        self.thumb_job_queue.queue.clear()

        if is_shutdown:
            return

        self.main_window.setWindowTitle(self.base_title)
        self.frame_content.clear()
        self._results_state = None
        self.selection.clear()
        if self.color_manager_panel:
            self.color_manager_panel.reset()

        if hasattr(self, "library_info_window"):
            self.library_info_window.close()

        self.main_window.thumb_grid.set_entries([])
        self.main_window.browsing_area.toggle_landing_page(enabled=True)
        self.main_window.browsing_area.landing_widget.animate_logo_in()
        self.main_window.browsing_area.pagination.setHidden(True)
        self.main_window.menu_bar.set_library_actions_enabled(False)

        # NOTE: Doesn't try to disable during tests
        if self.main_window.menu_bar.add_tag_to_selected_action:
            self.main_window.menu_bar.add_tag_to_selected_action.setEnabled(False)

    def backup_library(self):
        logger.info("[QtDriver] Backing up library...")
        Library.save_library_backup_to_disk(unwrap(self.lib.library_dir))

    def add_tag_action_callback(self):
        panel = EditTagPanel(self.lib)
        self.modal = Modal(
            panel,
            Translations["tag.new"],
            Translations["tag.create"],
            is_savable=True,
        )

        self.modal.saved.connect(
            lambda: (
                self.lib.add_tag(
                    panel.build_tag(),
                    set(panel.parent_ids),
                    set(panel.aliases),
                    set(panel.exclusion_ids),
                ),
                self.modal.hide(),
            )
        )
        self.modal.show()

    def search_for_tag_callback(self, tag_id: int) -> None:
        """Callback to search for a given Tag ID."""
        self.main_window.search_bar.set_query(f"tag_id:{tag_id}")
        self.update_browsing_state(BrowsingState.from_tag_id(tag_id, self.browsing_history.current))

    def add_tags_to_selected_callback(self, tag_ids: list[int]):
        self.entry_state.add_tags(self.selection.selected, tag_ids)

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
                entry = unwrap(self.lib.get_entry(item))
                filepath: Path = entry.path
                pending.append((item, filepath))

        if pending and self.delete_file_confirmation(len(pending), pending[0][1]):
            for e_id, f in pending:
                if (origin_path == f) or (not origin_path):
                    self.main_window.inspector.stop_media_playback()

                if e_id is not None:
                    self.lib.remove_entries([e_id])
                delete_file(library_dir / f)

            self.selection.clear()
            self.update_browsing_state()

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
        iterator = FunctionIterator(generator)
        iterator.value.connect(on_progress)
        runnable = CustomRunnable(iterator.run)
        runnable.done.connect(on_done)
        self._sync_pool.start(runnable)

    def _wait_for_sync_stop(self) -> None:
        """Block until a currently running sync is stopped, if any."""
        self._sync_pool.waitForDone()

    def sync_library_callback(self):
        """Run when syncing a Library is initiated."""
        if self.file_scan_lock:
            logger.info("[QtDriver] Sync already in progress, ignoring request")
            return
        self.file_scan_lock = True
        session_id = self._new_sync_session()
        # Disable the "Fix Unlinked Entries" modal's relink/remove actions during the sync
        if hasattr(self, "unlinked_modal") and self.unlinked_modal.isVisible():
            self.unlinked_modal.update_unlinked_count()

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
            sync_banner.set_scanning(searched_count + 1, found_count)

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

        self.file_scan_lock = False
        self.lib.unlinked_entries_count = unlinked_count
        if hasattr(self, "unlinked_modal") and self.unlinked_modal.isVisible():
            self.unlinked_modal.update_unlinked_count()
            self.unlinked_modal.remove_modal.refresh_list()
        if hasattr(self, "library_info_window") and self.library_info_window.isVisible():
            self.library_info_window.update_cleanup()

        if self.sync_engine.cancelled:
            return

        if (sync_banner := self._sync_banner) is not None:
            sync_banner.finish(new_count, unlinked_count, relinked_count)

    # TODO: Break this out of the driver with other thumbnail grid stuff.
    @property
    def page_size(self) -> int:
        """The max page size setting, or number of current results with infinite scroll on."""
        return len(self.frame_content) if self.settings.infinite_scroll else self.settings.page_size

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
        self.update_browsing_state()
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
        self.open_settings_modal()

    def open_fix_unlinked_entries_modal(self):
        if not hasattr(self, "unlinked_modal"):
            self.unlinked_modal = FixUnlinkedEntriesModal(self.lib, self)
        self.unlinked_modal.show()

    def sync_entry_stats_runnable(
        self,
        engine: LibrarySyncEngine,
        new_count: int,
        unlinked_count: int,
        relinked_count: int,
        session_id: int,
    ):
        """Refresh cached stat() data for files already known to the library.

        Threaded method.
        """
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
        """Adds any known new files to the library and run default macros on them.

        Threaded method.
        """
        if self._is_sync_stale(session_id):
            return
        new_count = engine.new_file_count
        unlinked_count = engine.unlinked_entries_count
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
        self.update_browsing_state(self.browsing_history.current.with_sorting_direction(ascending))

    def sorting_mode_callback(self, mode: SortingModeEnum):
        logger.info("[QtDriver] Sorting Mode Changed", mode=mode)
        self.update_browsing_state(self.browsing_history.current.with_sorting_mode(mode))

    def show_hidden_entries_callback(self, show_hidden_entries: bool):
        logger.info("[QtDriver] Show Hidden Entries Changed", exclude=show_hidden_entries)
        self.update_browsing_state(
            self.browsing_history.current.with_show_hidden_entries(show_hidden_entries)
        )

    def page_move(self, value: int, absolute: bool = False) -> None:
        current = self.browsing_history.current
        index = clamp(value if absolute else current.page_index + value, 0, self.pages_count - 1)
        if index != current.page_index:
            self.update_browsing_state(current.with_page_index(index))

    def navigation_callback(self, delta: int) -> None:
        """Callback for the Forwards and Backwards Navigation Buttons next to the search bar."""
        logger.info(
            "navigation_callback",
            delta=delta,
        )

        if self.browsing_history.move(delta):
            self.update_browsing_state()

    def copy_fields_action_callback(self):
        if len(self.selection.selected) > 0:
            entry = self.lib.get_entry_full(self.selection.selected[0])
            if entry:
                self.copy_buffer["fields"] = entry.fields
                self.copy_buffer["tags"] = [tag.id for tag in entry.tags]
        self.set_clipboard_menu_viability()

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

    def _on_selection_changed(self) -> None:
        self.set_clipboard_menu_viability()
        self.set_select_actions_visibility()

    def set_clipboard_menu_viability(self):
        if len(self.selection.selected) == 1:
            self.main_window.menu_bar.copy_fields_action.setEnabled(True)
        else:
            self.main_window.menu_bar.copy_fields_action.setEnabled(False)
        if self.selection.selected and (self.copy_buffer["fields"] or self.copy_buffer["tags"]):
            self.main_window.menu_bar.paste_fields_action.setEnabled(True)
        else:
            self.main_window.menu_bar.paste_fields_action.setEnabled(False)

    def set_select_actions_visibility(self):
        if not self.main_window.menu_bar.add_tag_to_selected_action:
            return

        if self.frame_content:
            self.main_window.menu_bar.select_all_action.setEnabled(True)
            self.main_window.menu_bar.select_inverse_action.setEnabled(True)
        else:
            self.main_window.menu_bar.select_all_action.setEnabled(False)
            self.main_window.menu_bar.select_inverse_action.setEnabled(False)

        if self.selection.selected:
            self.main_window.menu_bar.add_tag_to_selected_action.setEnabled(True)
            self.main_window.menu_bar.clear_select_action.setEnabled(True)
            self.main_window.menu_bar.delete_file_action.setEnabled(True)
        else:
            self.main_window.menu_bar.add_tag_to_selected_action.setEnabled(False)
            self.main_window.menu_bar.clear_select_action.setEnabled(False)
            self.main_window.menu_bar.delete_file_action.setEnabled(False)

    def update_thumbs(self):
        """Update search thumbnails."""
        with self.thumb_job_queue.mutex:
            # Cancels all thumb jobs waiting to be started
            self.thumb_job_queue.queue.clear()
            self.thumb_job_queue.all_tasks_done.notify_all()
            self.thumb_job_queue.not_full.notify_all()

        start = self.browsing_history.current.page_index * self.page_size
        end = min(start + self.page_size, len(self.frame_content))

        self.main_window.thumb_grid.set_entries(self.frame_content[start:end])
        self.main_window.update()

    def update_browsing_state(self, state: BrowsingState | None = None) -> None:
        """Navigates to a new BrowsingState when state is given, otherwise updates the results."""
        if not self.lib.library_dir:
            logger.info("Library not loaded")
            return

        previous = self.browsing_history.current
        if state:
            self.browsing_history.push(state)
        current = self.browsing_history.current

        self.main_window.search_bar.set_query(current.query or "")

        shown = self._results_state
        if current is shown:  # Results refresh in case entries were removed from the library
            selected = self.selection.selected
            self.selection.deselect(self.lib.removed_entry_ids(selected))
        only_page_changed = (
            current is not shown  # Refreshing the shown state searches again
            and shown is not None
            and current.with_page_index(0) == shown.with_page_index(0)
        )
        if not only_page_changed:
            # Search the library
            start_time = time.time()
            Ignore.get_patterns(self.lib.library_dir, include_global=True)
            results = self.lib.search_library(current, page_size=0)
            logger.info("items to render", count=len(results))
            end_time = time.time()

            # Show search result labels
            time_span = (
                f"<a style=color:'gray'>({format_timespan(end_time - start_time).title()})</a>"
            )
            count = f"<b>{results.total_count:,}</b>"
            is_single = results.total_count == 1
            # Show "X Results" on query, otherwise "X Items"
            if current.query:
                key = "status.results_found.singular" if is_single else "status.results_found"
            else:
                key = "status.items.singular" if is_single else "status.items"
            self.main_window.set_results_text(
                Translations.format(key, count=count, time_span=time_span)
            )
            self.frame_content = results.ids
            self.set_select_actions_visibility()
        self._results_state = current

        # Update page content
        same_page = current.query == previous.query and current.page_index == previous.page_index
        if state is None:
            entry_id = current.first_visible_entry_id
        elif same_page and current is not previous:
            # Keep the selection in view when the same results are only resorted or filtered
            entry_id = self.selection.cursor
        else:
            entry_id = None
        if entry_id is not None:
            self.main_window.thumb_grid.scroll_to(entry_id)
        self.update_thumbs()

        # Update pagination
        page_size = 0 if self.settings.infinite_scroll else self.settings.page_size
        if page_size > 0:
            self.pages_count = math.ceil(len(self.frame_content) / page_size)
        else:
            self.pages_count = 1
        self.main_window.browsing_area.pagination.update_buttons(
            self.pages_count, self.browsing_history.current.page_index, emit=False
        )

    def remove_recent_library(self, item_key: str):
        self.cached_values.beginGroup(AppCacheItems.LIBS_LIST)
        self.cached_values.remove(item_key)
        self.cached_values.endGroup()
        self.cached_values.sync()

    def update_libs_list(self, path: Path | str):
        """Add library to list in SettingItems.LIBS_LIST."""
        item_limit: int = 10
        path = Path(path)

        self.cached_values.beginGroup(AppCacheItems.LIBS_LIST)

        all_libs = {str(time.time()): str(path)}

        for item_key in self.cached_values.allKeys():
            item_path = str(self.cached_values.value(item_key, type=str))
            if Path(item_path) != path:
                all_libs[item_key] = item_path

        # sort items, most recent first
        all_libs_list = sorted(all_libs.items(), key=lambda item: item[0], reverse=True)

        # remove previously saved items
        self.cached_values.remove("")

        for item_key, item_value in all_libs_list[:item_limit]:
            self.cached_values.setValue(item_key, item_value)

        self.cached_values.endGroup()
        self.cached_values.sync()
        self.update_recent_lib_menu()

    def update_recent_lib_menu(self):
        """Updates the recent library menu from the latest values from the settings file."""
        lib_items: dict[str, tuple[str, str]] = {}

        # get recent libraries sorted by timestamp
        self.cached_values.beginGroup(AppCacheItems.LIBS_LIST)
        for item_tstamp in self.cached_values.allKeys():
            val = str(self.cached_values.value(item_tstamp, type=str))
            cut_val = val
            if len(val) > 45:
                cut_val = f"{val[0:10]} ... {val[-10:]}"
            lib_items[item_tstamp] = (val, cut_val)

        # Sort lib_items by the key
        libs_sorted = sorted(lib_items.items(), key=lambda item: item[0], reverse=True)
        self.cached_values.endGroup()

        self.main_window.menu_bar.rebuild_open_recent_library_menu(
            [Path(key[1][0]) for key in libs_sorted],
            self.settings.show_filepath,  # TODO: once QtDriver is a Singleton remove this parameter
            self.open_library,
            self.clear_recent_libs,
        )

    def clear_recent_libs(self):
        """Clear the list of recent libraries from the settings file."""
        cache = self.cached_values
        cache.beginGroup(AppCacheItems.LIBS_LIST)
        self.cached_values.remove("")
        self.cached_values.endGroup()
        self.cached_values.sync()
        self.update_recent_lib_menu()

    def open_settings_modal(self):
        SettingsPanel.build_modal(self).show()

    def check_for_update(self):
        """Check for an update to TagStudio and display a message box if there is one."""
        latest_version = TagStudioCore.get_most_recent_release_version()
        if latest_version == str(self.cached_values.value(AppCacheItems.DISMISSED_UPDATE)):
            return

        if latest_version and is_version_outdated(VERSION, latest_version):
            update_box = UpdateAvailableMessageBox()
            update_box.button(QMessageBox.StandardButton.Ignore).clicked.connect(
                partial(self.dismiss_update, str(latest_version))
            )
            update_box.exec()

    def _record_program_version(self) -> bool:
        """Record the version of the program to the cache file.

        Returns:
            bool: True if the current version is newer than the previously recorded one.
                Will be False on first time runs of the program, and True if it's not the first run
                but there's no existing record of the last version used.
        """
        is_first_run = not self.cached_values.allKeys()  # No cache keys means this is a first run
        last_version_opened = self.cached_values.value(AppCacheItems.LAST_VERSION_OPENED)
        self.cached_values.setValue(AppCacheItems.LAST_VERSION_OPENED, VERSION)
        self.cached_values.sync()

        if is_first_run:
            return False
        if not last_version_opened:
            return True
        try:
            return semver.Version.parse(str(last_version_opened)) < semver.Version.parse(VERSION)
        except ValueError:
            return str(last_version_opened) != VERSION

    def show_changelog(self):
        if not hasattr(self, "changelog_modal"):
            self.changelog_modal = Modal(
                ChangelogModal(),
                window_title=Translations["changelog.window_title"],
                inline_title=False,
            )
        self.changelog_modal.show()

    def dismiss_update(self, version: str):
        """Dismiss an update notification for a specific new version of TagStudio."""
        self.cached_values.setValue(AppCacheItems.DISMISSED_UPDATE, version)

    def open_library(self, path: Path) -> None:
        """Open a TagStudio library."""
        library_dir_display = (
            path if self.settings.show_filepath == ShowFilepathOption.SHOW_FULL_PATHS else path.name
        )
        message = Translations.format("splash.opening_library", library_path=library_dir_display)
        self.main_window.browsing_area.landing_widget.set_status_label(message)
        self.main_window.repaint()

        if self.lib.library_dir:
            self.close_library()

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
            logger.error(e)
            open_status = OpenLibraryResult(
                success=False, library_path=path, error_description=f"{type(e).__name__}: {e}"
            )
        self.cache_manager = CacheManager(
            path,
            max_size=self.settings.thumb_cache_size,
            img_quality=self.settings.cached_thumb_quality,
        )
        cache_size = self.settings.thumb_cache_size * self.cache_manager.STAT_MULTIPLIER
        logger.info(
            f"[Config] Thumbnail Cache Size: {format_size(cache_size)}",
        )

        # Migration is required
        if open_status.needs_json_migration:
            self.migration_modal = JsonMigrationModal(path)
            self.migration_modal.migration_finished.connect(
                lambda: self._init_library(path, self.lib.open_library(path))
            )
            self.main_window.browsing_area.landing_widget.set_status_label("")
            self.migration_modal.paged_panel.show()
        else:
            self._init_library(path, open_status)

    def _init_library(self, path: Path, open_status: OpenLibraryResult):
        if not open_status.success:
            self.show_error_message(
                error_name=open_status.error_title
                or Translations["window.message.error_opening_library"],
                error_desc=open_status.error_description,
            )
            return open_status

        assert self.lib.library_dir
        self.init_workers()
        Ignore.get_patterns(self.lib.library_dir, include_global=True)
        self.__reset_navigation()

        if self.settings.scan_files_on_open:
            self.sync_library_callback()
        elif not self._sync_disabled_notice_shown:
            self._sync_disabled_notice_shown = True
            # Show that the setting for opening a library on start is turned off,
            # with a prompt to open the settings to change that (encouraged but not required).
            self._create_sync_banner().set_disabled_notice()

        if self.settings.show_filepath == ShowFilepathOption.SHOW_FULL_PATHS:
            library_dir_display = self.lib.library_dir
        else:
            library_dir_display = self.lib.library_dir.name

        self.update_libs_list(path)
        self.cached_values.setValue(AppCacheItems.LAST_LIBRARY, str(self.lib.library_dir))
        self.cached_values.sync()
        self.main_window.setWindowTitle(
            Translations.format(
                "app.title",
                base_title=self.base_title,
                library_dir=library_dir_display,
            )
        )
        self.main_window.setAcceptDrops(True)

        self.init_ignore_modal()

        self.main_window.menu_bar.set_library_actions_enabled(True)

        self.main_window.inspector.update_from_selection()

        # page (re)rendering, extract eventually
        initial_state = BrowsingState(
            page_index=0,
            sorting_mode=self.main_window.sorting_mode,
            ascending=self.main_window.sorting_direction,
        )
        self.update_browsing_state(initial_state)

        self.main_window.browsing_area.toggle_landing_page(enabled=False)
        self.main_window.thumb_grid.scroll_area.setFocus()
        return open_status

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
