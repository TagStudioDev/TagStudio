# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

# SIGTERM handling based on the implementation by Virgil Dupras for dupeGuru:
# https://github.com/arsenetar/dupeguru/blob/master/run.py#L71


"""A Qt driver for TagStudio."""

import contextlib
import ctypes
import math
import os
import platform
import re
import sys
import time
from argparse import Namespace
from pathlib import Path
from queue import Queue
from shutil import which
from typing import Generic, TypeVar
from warnings import catch_warnings

import structlog
from humanfriendly import format_size, format_timespan
from PySide6.QtCore import QObject, QSettings, Qt, QThread, QThreadPool, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QFontDatabase,
    QGuiApplication,
    QIcon,
    QMouseEvent,
    QPalette,
)
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMessageBox,
    QPushButton,
    QScrollArea,
)

# this import has side-effect of import PySide resources
import tagstudio.qt.resources_rc  # noqa: F401
from tagstudio.core.constants import TAG_ARCHIVED, TAG_FAVORITE, VERSION, VERSION_BRANCH
from tagstudio.core.driver import DriverMixin
from tagstudio.core.enums import MacroID, SettingItems, ShowFilepathOption
from tagstudio.core.global_settings import DEFAULT_GLOBAL_SETTINGS_PATH, GlobalSettings, Theme
from tagstudio.core.library.alchemy.enums import (
    BrowsingState,
    FieldTypeEnum,
    ItemType,
    SortingModeEnum,
)
from tagstudio.core.library.alchemy.fields import _FieldID
from tagstudio.core.library.alchemy.library import Library, LibraryStatus
from tagstudio.core.library.alchemy.models import Entry
from tagstudio.core.media_types import MediaCategories
from tagstudio.core.palette import ColorType, UiColor, get_ui_color
from tagstudio.core.query_lang.util import ParsingError
from tagstudio.core.ts_core import TagStudioCore
from tagstudio.core.utils.refresh_dir import RefreshDirTracker
from tagstudio.core.utils.web import strip_web_protocol
from tagstudio.qt.cache_manager import CacheManager
from tagstudio.qt.helpers.custom_runnable import CustomRunnable
from tagstudio.qt.helpers.file_deleter import delete_file
from tagstudio.qt.helpers.function_iterator import FunctionIterator
from tagstudio.qt.helpers.vendored.ffmpeg import FFMPEG_CMD, FFPROBE_CMD
from tagstudio.qt.main_window import MainWindow
from tagstudio.qt.modals.about import AboutModal
from tagstudio.qt.modals.build_tag import BuildTagPanel
from tagstudio.qt.modals.drop_import import DropImportModal
from tagstudio.qt.modals.ffmpeg_checker import FfmpegChecker
from tagstudio.qt.modals.file_extension import FileExtensionModal
from tagstudio.qt.modals.fix_dupes import FixDupeFilesModal
from tagstudio.qt.modals.fix_unlinked import FixUnlinkedEntriesModal
from tagstudio.qt.modals.folders_to_tags import FoldersToTagsModal
from tagstudio.qt.modals.settings_panel import SettingsPanel
from tagstudio.qt.modals.tag_color_manager import TagColorManager
from tagstudio.qt.modals.tag_database import TagDatabasePanel
from tagstudio.qt.modals.tag_search import TagSearchPanel
from tagstudio.qt.platform_strings import trash_term
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.splash import Splash
from tagstudio.qt.translations import Translations
from tagstudio.qt.widgets.item_thumb import BadgeType, ItemThumb
from tagstudio.qt.widgets.migration_modal import JsonMigrationModal
from tagstudio.qt.widgets.panel import PanelModal
from tagstudio.qt.widgets.progress import ProgressWidget
from tagstudio.qt.widgets.thumb_renderer import ThumbRenderer

BADGE_TAGS = {
    BadgeType.FAVORITE: TAG_FAVORITE,
    BadgeType.ARCHIVED: TAG_ARCHIVED,
}


# SIGQUIT is not defined on Windows
if sys.platform == "win32":
    from signal import SIGINT, SIGTERM, signal

    SIGQUIT = SIGTERM
else:
    from signal import SIGINT, SIGQUIT, SIGTERM, signal

logger = structlog.get_logger(__name__)


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


T = TypeVar("T")


# Ex. User visits | A ->[B]     |
#                 | A    B ->[C]|
#                 | A   [B]<- C |
#                 |[A]<- B    C |  Previous routes still exist
#                 | A ->[D]     |  Stack is cut from [:A] on new route
class History(Generic[T]):
    __history: list[T]
    __index: int = 0

    def __init__(self, initial_value: T):
        self.__history = [initial_value]
        super().__init__()

    def erase_future(self) -> None:
        self.__history = self.__history[: self.__index + 1]

    def push(self, value: T) -> None:
        self.erase_future()
        self.__history.append(value)
        self.__index = len(self.__history) - 1

    def move(self, delta: int):
        self.__index = clamp(self.__index + delta, 0, len(self.__history) - 1)

    @property
    def current(self) -> T:
        return self.__history[self.__index]


class QtDriver(DriverMixin, QObject):
    """A Qt GUI frontend driver for TagStudio."""

    SIGTERM = Signal()

    tag_manager_panel: PanelModal | None = None
    color_manager_panel: TagColorManager | None = None
    file_extension_panel: PanelModal | None = None
    tag_search_panel: TagSearchPanel | None = None
    add_tag_modal: PanelModal | None = None
    folders_modal: FoldersToTagsModal
    about_modal: AboutModal
    unlinked_modal: FixUnlinkedEntriesModal
    dupe_modal: FixDupeFilesModal

    applied_theme: Theme

    lib: Library

    browsing_history: History[BrowsingState]

    def __init__(self, args: Namespace):
        super().__init__()
        # prevent recursive badges update when multiple items selected
        self.badge_update_lock = False
        self.lib = Library()
        self.rm: ResourceManager = ResourceManager()
        self.args = args
        self.frame_content: list[int] = []  # List of Entry IDs on the current page
        self.pages_count = 0

        self.scrollbar_pos = 0
        self.spacing = None

        self.branch: str = (" (" + VERSION_BRANCH + ")") if VERSION_BRANCH else ""
        self.base_title: str = f"TagStudio Alpha {VERSION}{self.branch}"
        # self.title_text: str = self.base_title
        # self.buffer = {}
        self.thumb_job_queue: Queue = Queue()
        self.thumb_threads: list[Consumer] = []
        self.thumb_cutoff: float = time.time()
        self.selected: list[int] = []  # Selected Entry IDs

        self.SIGTERM.connect(self.handle_sigterm)

        self.global_settings_path = DEFAULT_GLOBAL_SETTINGS_PATH
        if self.args.settings_file:
            self.global_settings_path = Path(self.args.settings_file)
        else:
            logger.info("[Settings] Global Settings File Path not specified, using default")
        self.settings = GlobalSettings.read_settings(self.global_settings_path)
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

        # NOTE: This should be a per-library setting rather than an application setting.
        thumb_cache_size_limit: int = int(
            str(
                self.cached_values.value(
                    SettingItems.THUMB_CACHE_SIZE_LIMIT,
                    defaultValue=CacheManager.size_limit,
                    type=int,
                )
            )
        )

        CacheManager.size_limit = thumb_cache_size_limit
        self.cached_values.setValue(SettingItems.THUMB_CACHE_SIZE_LIMIT, CacheManager.size_limit)
        self.cached_values.sync()
        logger.info(
            f"[Config] Thumbnail cache size limit: {format_size(CacheManager.size_limit)}",
        )

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
            dir="/",
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
        if self.settings.theme == Theme.SYSTEM:
            # TODO: detect theme instead of always setting dark
            self.app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
        else:
            self.app.styleHints().setColorScheme(
                Qt.ColorScheme.Dark if self.settings.theme == Theme.DARK else Qt.ColorScheme.Light
            )

        if (
            platform.system() == "Darwin" or platform.system() == "Windows"
        ) and QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark:
            pal: QPalette = self.app.palette()
            pal.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.Window, QColor("#1e1e1e"))
            pal.setColor(QPalette.ColorGroup.Normal, QPalette.ColorRole.Button, QColor("#1e1e1e"))
            pal.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Window, QColor("#232323"))
            pal.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Button, QColor("#232323"))
            pal.setColor(
                QPalette.ColorGroup.Inactive, QPalette.ColorRole.ButtonText, QColor("#666666")
            )

            self.app.setPalette(pal)

        # Handle OS signals
        self.setup_signals()
        # allow to process input from console, eg. SIGTERM
        timer = QTimer()
        timer.start(500)
        timer.timeout.connect(lambda: None)

        # self.main_window = loader.load(home_path)
        self.main_window = MainWindow(self)
        self.main_window.setWindowTitle(self.base_title)
        self.main_window.mousePressEvent = self.mouse_navigation
        self.main_window.dragEnterEvent = self.drag_enter_event
        self.main_window.dragMoveEvent = self.drag_move_event
        self.main_window.dropEvent = self.drop_event

        self.splash: Splash = Splash(
            resource_manager=self.rm,
            screen_width=QGuiApplication.primaryScreen().geometry().width(),
            splash_name="",  # TODO: Get splash name from config
            device_ratio=self.main_window.devicePixelRatio(),
        )
        self.splash.show()

        if os.name == "nt":
            appid = "cyanvoxel.tagstudio.9"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)  # type: ignore[attr-defined,unused-ignore]

        self.app.setApplicationName("tagstudio")
        self.app.setApplicationDisplayName("TagStudio")
        if platform.system() != "Darwin":
            fallback_icon = QIcon()
            fallback_icon.addFile(str(self.rm.get_path("icon")))
            self.app.setWindowIcon(QIcon.fromTheme("tagstudio", fallback_icon))

            if platform.system() != "Windows":
                self.app.setDesktopFileName("tagstudio")

        # Initialize the Tag Manager panel
        self.tag_manager_panel = PanelModal(
            widget=TagDatabasePanel(self, self.lib),
            done_callback=lambda: self.main_window.preview_panel.update_widgets(
                update_preview=False
            ),
            has_save=False,
        )
        self.tag_manager_panel.setTitle(Translations["tag_manager.title"])
        self.tag_manager_panel.setWindowTitle(Translations["tag_manager.title"])

        # Initialize the Color Group Manager panel
        self.color_manager_panel = TagColorManager(self)

        # Initialize the Tag Search panel
        self.tag_search_panel = TagSearchPanel(self.lib, is_tag_chooser=True)
        self.tag_search_panel.set_driver(self)
        self.add_tag_modal = PanelModal(
            widget=self.tag_search_panel,
            title=Translations["tag.add.plural"],
            window_title=Translations["tag.add.plural"],
        )
        self.tag_search_panel.tag_chosen.connect(
            lambda t: (
                self.add_tags_to_selected_callback(t),
                self.main_window.preview_panel.update_widgets(),
            )
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

        # Settings...
        self.main_window.menu_bar.settings_action.triggered.connect(self.open_settings_modal)

        # Open Library on Start
        self.main_window.menu_bar.open_on_start_action.setChecked(
            self.settings.open_last_loaded_on_startup
        )

        def set_open_last_loaded_on_startup(checked: bool):
            self.settings.open_last_loaded_on_startup = checked
            self.settings.save()

        self.main_window.menu_bar.open_on_start_action.triggered.connect(
            set_open_last_loaded_on_startup
        )

        # Refresh Directories
        self.main_window.menu_bar.refresh_dir_action.triggered.connect(
            lambda: self.call_if_library_open(self.add_new_files_callback)
        )

        # Close Library
        self.main_window.menu_bar.close_library_action.triggered.connect(self.close_library)

        # endregion

        # region Edit Menu ============================================================
        self.main_window.menu_bar.new_tag_action.triggered.connect(
            lambda: self.add_tag_action_callback()
        )

        self.main_window.menu_bar.select_all_action.triggered.connect(
            self.select_all_action_callback
        )

        self.main_window.menu_bar.select_inverse_action.triggered.connect(
            self.select_inverse_action_callback
        )

        self.main_window.menu_bar.clear_select_action.triggered.connect(
            self.clear_select_action_callback
        )

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

        self.main_window.menu_bar.tag_manager_action.triggered.connect(self.tag_manager_panel.show)

        self.main_window.menu_bar.color_manager_action.triggered.connect(
            self.color_manager_panel.show
        )

        # endregion

        # region View Menu ============================================================

        def on_show_filenames_action(checked: bool):
            self.settings.show_filenames_in_grid = checked
            self.settings.save()
            self.show_grid_filenames(checked)

        self.main_window.menu_bar.show_filenames_action.triggered.connect(on_show_filenames_action)
        self.main_window.menu_bar.show_filenames_action.setChecked(
            self.settings.show_filenames_in_grid
        )

        # endregion

        # region Tools Menu ===========================================================
        def create_fix_unlinked_entries_modal():
            if not hasattr(self, "unlinked_modal"):
                self.unlinked_modal = FixUnlinkedEntriesModal(self.lib, self)
            self.unlinked_modal.show()

        self.main_window.menu_bar.fix_unlinked_entries_action.triggered.connect(
            create_fix_unlinked_entries_modal
        )

        def create_dupe_files_modal():
            if not hasattr(self, "dupe_modal"):
                self.dupe_modal = FixDupeFilesModal(self.lib, self)
            self.dupe_modal.show()

        self.main_window.menu_bar.fix_dupe_files_action.triggered.connect(create_dupe_files_modal)

        # TODO: Move this to a settings screen.
        self.main_window.menu_bar.clear_thumb_cache_action.triggered.connect(
            lambda: CacheManager.clear_cache(self.lib.library_dir)
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

        # endregion

        # endregion

        self.main_window.search_field.textChanged.connect(self.update_completions_list)

        self.main_window.preview_panel.fields.archived_updated.connect(
            lambda hidden: self.update_badges(
                {BadgeType.ARCHIVED: hidden}, origin_id=0, add_tags=False
            )
        )
        self.main_window.preview_panel.fields.favorite_updated.connect(
            lambda hidden: self.update_badges(
                {BadgeType.FAVORITE: hidden}, origin_id=0, add_tags=False
            )
        )

        QFontDatabase.addApplicationFont(
            str(Path(__file__).parents[1] / "resources/qt/fonts/Oxanium-Bold.ttf")
        )

        self.item_thumbs: list[ItemThumb] = []
        self.thumb_renderers: list[ThumbRenderer] = []
        self.init_library_window()
        self.migration_modal: JsonMigrationModal = None

        path_result = self.evaluate_path(str(self.args.open).lstrip().rstrip())
        if path_result.success and path_result.library_path:
            self.open_library(path_result.library_path)
        elif self.settings.open_last_loaded_on_startup:
            # evaluate_path() with argument 'None' returns a LibraryStatus for the last library
            path_result = self.evaluate_path(None)
            if path_result.success and path_result.library_path:
                self.open_library(path_result.library_path)

        # Check if FFmpeg or FFprobe are missing and show warning if so
        if not which(FFMPEG_CMD) or not which(FFPROBE_CMD):
            FfmpegChecker().show()

        self.app.exec()
        self.shutdown()

    def show_error_message(self, error_name: str, error_desc: str | None = None):
        self.main_window.status_bar.showMessage(error_name, Qt.AlignmentFlag.AlignLeft)
        self.main_window.landing_widget.set_status_label(error_name)
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

        def _update_browsing_state():
            try:
                self.update_browsing_state(
                    BrowsingState.from_search_query(self.main_window.search_field.text())
                    .with_sorting_mode(self.main_window.sorting_mode)
                    .with_sorting_direction(self.main_window.sorting_direction)
                )
            except ParsingError as e:
                self.main_window.status_bar.showMessage(
                    f"{Translations['status.results.invalid_syntax']} "
                    f'"{self.main_window.search_field.text()}"'
                )
                logger.error("[QtDriver] Could not update BrowsingState", error=e)

        # Search Button
        self.main_window.search_button.clicked.connect(_update_browsing_state)

        # Search Field
        self.main_window.search_field.returnPressed.connect(_update_browsing_state)

        # Sorting Dropdowns
        self.main_window.sorting_mode_combobox.setCurrentIndex(
            list(SortingModeEnum).index(self.browsing_history.current.sorting_mode)
        )
        self.main_window.sorting_mode_combobox.currentIndexChanged.connect(
            self.sorting_mode_callback
        )

        self.main_window.sorting_direction_combobox.currentIndexChanged.connect(
            self.sorting_direction_callback
        )

        # Thumbnail Size ComboBox
        self.main_window.thumb_size_combobox.currentIndexChanged.connect(
            lambda: self.thumb_size_callback(self.main_window.thumb_size_combobox.currentData())
        )
        self._update_thumb_count()

        self.main_window.back_button.clicked.connect(lambda: self.navigation_callback(-1))
        self.main_window.forward_button.clicked.connect(lambda: self.navigation_callback(1))

        # NOTE: Putting this early will result in a white non-responsive
        # window until everything is loaded. Consider adding a splash screen
        # or implementing some clever loading tricks.
        self.main_window.show()
        self.main_window.activateWindow()
        self.main_window.toggle_landing_page(enabled=True)

        self.main_window.pagination.index.connect(lambda i: self.page_move(i, absolute=True))

        self.splash.finish(self.main_window)

    def init_file_extension_manager(self):
        """Initialize the File Extension panel."""
        if self.file_extension_panel:
            with catch_warnings(record=True):
                self.main_window.menu_bar.manage_file_ext_action.triggered.disconnect()
                self.file_extension_panel.saved.disconnect()
            self.file_extension_panel.deleteLater()
            self.file_extension_panel = None

        panel = FileExtensionModal(self.lib)
        self.file_extension_panel = PanelModal(
            panel,
            has_save=True,
        )
        self.file_extension_panel.setTitle(Translations["ignore_list.title"])
        self.file_extension_panel.setWindowTitle(Translations["ignore_list.title"])
        self.file_extension_panel.saved.connect(
            lambda: (panel.save(), self.update_browsing_state())
        )
        self.main_window.menu_bar.manage_file_ext_action.triggered.connect(
            self.file_extension_panel.show
        )

    def show_grid_filenames(self, value: bool):
        for thumb in self.item_thumbs:
            thumb.set_filename_visibility(value)

    def call_if_library_open(self, func):
        """Check if loaded library has valid path before executing the button function."""
        if self.lib.library_dir:
            func()

    def handle_sigterm(self):
        self.shutdown()

    def shutdown(self):
        """Save Library on Application Exit."""
        self.close_library(is_shutdown=True)
        logger.info("[SHUTDOWN] Ending Thumbnail Threads...")
        for _ in self.thumb_threads:
            self.thumb_job_queue.put(Consumer.MARKER_QUIT)

        # wait for threads to quit
        for thread in self.thumb_threads:
            thread.quit()
            thread.wait()

        QApplication.quit()

    def close_library(self, is_shutdown: bool = False):
        if not self.lib.library_dir:
            logger.info("No Library to Close")
            return

        logger.info("Closing Library...")
        self.main_window.status_bar.showMessage(Translations["status.library_closing"])
        start_time = time.time()

        self.cached_values.setValue(SettingItems.LAST_LIBRARY, str(self.lib.library_dir))
        self.cached_values.sync()

        # Reset library state
        self.main_window.preview_panel.update_widgets()
        self.main_window.search_field.setText("")
        scrollbar: QScrollArea = self.main_window.entry_scroll_area
        scrollbar.verticalScrollBar().setValue(0)
        self.__reset_navigation()

        self.lib.close()

        self.thumb_job_queue.queue.clear()
        if is_shutdown:
            # no need to do other things on shutdown
            return

        self.main_window.setWindowTitle(self.base_title)

        self.selected.clear()
        self.frame_content.clear()
        [x.set_mode(None) for x in self.item_thumbs]
        if self.color_manager_panel:
            self.color_manager_panel.reset()

        self.set_clipboard_menu_viability()
        self.set_select_actions_visibility()

        self.main_window.preview_panel.update_widgets()
        self.main_window.toggle_landing_page(enabled=True)
        self.main_window.pagination.setHidden(True)
        try:
            self.main_window.menu_bar.save_library_backup_action.setEnabled(False)
            self.main_window.menu_bar.close_library_action.setEnabled(False)
            self.main_window.menu_bar.refresh_dir_action.setEnabled(False)
            self.main_window.menu_bar.tag_manager_action.setEnabled(False)
            self.main_window.menu_bar.color_manager_action.setEnabled(False)
            self.main_window.menu_bar.manage_file_ext_action.setEnabled(False)
            self.main_window.menu_bar.new_tag_action.setEnabled(False)
            self.main_window.menu_bar.fix_unlinked_entries_action.setEnabled(False)
            self.main_window.menu_bar.fix_dupe_files_action.setEnabled(False)
            self.main_window.menu_bar.clear_thumb_cache_action.setEnabled(False)
            self.main_window.menu_bar.folders_to_tags_action.setEnabled(False)
        except AttributeError:
            logger.warning(
                "[Library] Could not disable library management menu actions. Is this in a test?"
            )

        # NOTE: Doesn't try to disable during tests
        if self.main_window.menu_bar.add_tag_to_selected_action:
            self.main_window.menu_bar.add_tag_to_selected_action.setEnabled(False)

        end_time = time.time()
        self.main_window.status_bar.showMessage(
            Translations.format(
                "status.library_closed", time_span=format_timespan(end_time - start_time)
            )
        )

    def backup_library(self):
        logger.info("Backing Up Library...")
        self.main_window.status_bar.showMessage(Translations["status.library_backup_in_progress"])
        start_time = time.time()
        target_path = self.lib.save_library_backup_to_disk()
        end_time = time.time()
        self.main_window.status_bar.showMessage(
            Translations.format(
                "status.library_backup_success",
                path=target_path,
                time_span=format_timespan(end_time - start_time),
            )
        )

    def add_tag_action_callback(self):
        panel = BuildTagPanel(self.lib)
        self.modal = PanelModal(
            panel,
            has_save=True,
        )
        self.modal.setTitle(Translations["tag.new"])
        self.modal.setWindowTitle(Translations["tag.add"])

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

    def select_all_action_callback(self):
        """Set the selection to all visible items."""
        self.selected.clear()
        for item in self.item_thumbs:
            if item.mode and item.item_id not in self.selected and not item.isHidden():
                self.selected.append(item.item_id)
                item.thumb_button.set_selected(True)

        self.set_clipboard_menu_viability()
        self.set_select_actions_visibility()

        self.main_window.preview_panel.update_widgets(update_preview=False)

    def select_inverse_action_callback(self):
        """Invert the selection of all visible items."""
        new_selected = []

        for item in self.item_thumbs:
            if item.mode and not item.isHidden():
                if item.item_id in self.selected:
                    item.thumb_button.set_selected(False)
                else:
                    item.thumb_button.set_selected(True)
                    new_selected.append(item.item_id)

        self.selected = new_selected

        self.set_clipboard_menu_viability()
        self.set_select_actions_visibility()

        self.main_window.preview_panel.update_widgets(update_preview=False)

    def clear_select_action_callback(self):
        self.selected.clear()
        self.set_select_actions_visibility()
        for item in self.item_thumbs:
            item.thumb_button.set_selected(False)

        self.set_clipboard_menu_viability()
        self.main_window.preview_panel.update_widgets()

    def add_tags_to_selected_callback(self, tag_ids: list[int]):
        self.lib.add_tags_to_entries(self.selected, tag_ids)

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
        pending: list[tuple[int, Path]] = []
        deleted_count: int = 0

        if len(self.selected) <= 1 and origin_path:
            origin_id_ = origin_id
            if not origin_id_:
                with contextlib.suppress(IndexError):
                    origin_id_ = self.selected[0]

            pending.append((origin_id_, Path(origin_path)))
        elif (len(self.selected) > 1) or (len(self.selected) <= 1):
            for item in self.selected:
                entry = self.lib.get_entry(item)
                filepath: Path = entry.path
                pending.append((item, filepath))

        if pending:
            return_code = self.delete_file_confirmation(len(pending), pending[0][1])
            # If there was a confirmation and not a cancellation
            if (
                return_code == QMessageBox.ButtonRole.DestructiveRole.value
                and return_code != QMessageBox.ButtonRole.ActionRole.value
            ):
                for i, tup in enumerate(pending):
                    e_id, f = tup
                    if (origin_path == f) or (not origin_path):
                        self.main_window.preview_panel.thumb.media_player.stop()
                    if delete_file(self.lib.library_dir / f):
                        self.main_window.status_bar.showMessage(
                            Translations.format(
                                "status.deleting_file", i=i, count=len(pending), path=f
                            )
                        )
                        self.main_window.status_bar.repaint()
                        self.lib.remove_entries([e_id])

                        deleted_count += 1
                self.selected.clear()

        if deleted_count > 0:
            self.update_browsing_state()
            self.main_window.preview_panel.update_widgets()

        if len(self.selected) <= 1 and deleted_count == 0:
            self.main_window.status_bar.showMessage(Translations["status.deleted_none"])
        elif len(self.selected) <= 1 and deleted_count == 1:
            self.main_window.status_bar.showMessage(
                Translations.format("status.deleted_file_plural", count=deleted_count)
            )
        elif len(self.selected) > 1 and deleted_count == 0:
            self.main_window.status_bar.showMessage(Translations["status.deleted_none"])
        elif len(self.selected) > 1 and deleted_count < len(self.selected):
            self.main_window.status_bar.showMessage(
                Translations.format("status.deleted_partial_warning", count=deleted_count)
            )
        elif len(self.selected) > 1 and deleted_count == len(self.selected):
            self.main_window.status_bar.showMessage(
                Translations.format("status.deleted_file_plural", count=deleted_count)
            )
        self.main_window.status_bar.repaint()

    def delete_file_confirmation(self, count: int, filename: Path | None = None) -> int:
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
        perm_warning: str = (
            f"<h4 style='color: {get_ui_color(ColorType.PRIMARY, UiColor.RED)}'>"
            f"{perm_warning_msg}</h4>"
        )

        msg = QMessageBox()
        msg.setStyleSheet("font-weight:normal;")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setWindowTitle(
            Translations["trash.title.singular"]
            if count == 1
            else Translations["trash.title.plural"]
        )
        msg.setIcon(QMessageBox.Icon.Warning)
        if count <= 1:
            msg_text = Translations.format(
                "trash.dialog.move.confirmation.singular", trash_term=trash_term()
            )
            msg.setText(
                f"<h3>{msg_text}</h3>"
                f"<h4>{Translations['trash.dialog.disambiguation_warning.singular']}</h4>"
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
                f"<h3>{msg_text}</h3>"
                f"<h4>{Translations['trash.dialog.disambiguation_warning.plural']}</h4>"
                f"{perm_warning}<br>"
            )

        yes_button: QPushButton = msg.addButton("&Yes", QMessageBox.ButtonRole.YesRole)
        msg.addButton("&No", QMessageBox.ButtonRole.NoRole)
        msg.setDefaultButton(yes_button)

        return msg.exec()

    def add_new_files_callback(self):
        """Run when user initiates adding new files to the Library."""
        tracker = RefreshDirTracker(self.lib)

        pw = ProgressWidget(
            cancel_button_text=None,
            minimum=0,
            maximum=0,
        )
        pw.setWindowTitle(Translations["library.refresh.title"])
        pw.update_label(Translations["library.refresh.scanning_preparing"])

        pw.show()

        iterator = FunctionIterator(lambda: tracker.refresh_dir(self.lib.library_dir))
        iterator.value.connect(
            lambda x: (
                pw.update_progress(x + 1),
                pw.update_label(
                    Translations.format(
                        "library.refresh.scanning.plural"
                        if x + 1 != 1
                        else "library.refresh.scanning.singular",
                        searched_count=f"{x + 1:n}",
                        found_count=f"{tracker.files_count:n}",
                    )
                ),
            )
        )
        r = CustomRunnable(iterator.run)
        r.done.connect(
            lambda: (
                pw.hide(),
                pw.deleteLater(),
                self.add_new_files_runnable(tracker),
            )
        )
        QThreadPool.globalInstance().start(r)

    def add_new_files_runnable(self, tracker: RefreshDirTracker):
        """Adds any known new files to the library and run default macros on them.

        Threaded method.
        """
        files_count = tracker.files_count

        iterator = FunctionIterator(tracker.save_new_files)
        pw = ProgressWidget(
            cancel_button_text=None,
            minimum=0,
            maximum=0,
        )
        pw.setWindowTitle(Translations["entries.running.dialog.title"])
        pw.update_label(
            Translations.format("entries.running.dialog.new_entries", total=f"{files_count:n}")
        )
        pw.show()

        iterator.value.connect(
            lambda: (
                pw.update_label(
                    Translations.format(
                        "entries.running.dialog.new_entries", total=f"{files_count:n}"
                    )
                ),
            )
        )
        r = CustomRunnable(iterator.run)
        r.done.connect(
            lambda: (
                pw.hide(),
                pw.deleteLater(),
                # refresh the library only when new items are added
                files_count and self.update_browsing_state(),  # type: ignore
            )
        )
        QThreadPool.globalInstance().start(r)

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
        entry: Entry = self.lib.get_entry(entry_id)
        full_path = self.lib.library_dir / entry.path
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

        elif name == MacroID.SIDECAR:
            parsed_items = TagStudioCore.get_gdl_sidecar(full_path, source)
            for field_id, value in parsed_items.items():
                if isinstance(value, list) and len(value) > 0 and isinstance(value[0], str):
                    value = self.lib.tag_from_strings(value)
                self.lib.add_field_to_entry(
                    entry.id,
                    field_id=field_id,
                    value=value,
                )

        elif name == MacroID.BUILD_URL:
            url = TagStudioCore.build_url(entry, source)
            if url is not None:
                self.lib.add_field_to_entry(entry.id, field_id=_FieldID.SOURCE, value=url)
        elif name == MacroID.MATCH:
            TagStudioCore.match_conditions(self.lib, entry.id)
        elif name == MacroID.CLEAN_URL:
            for field in entry.text_fields:
                if field.type.type == FieldTypeEnum.TEXT_LINE and field.value:
                    self.lib.update_entry_field(
                        entry_ids=entry.id,
                        field=field,
                        content=strip_web_protocol(field.value),
                    )

    def sorting_direction_callback(self):
        logger.info("Sorting Direction Changed", ascending=self.main_window.sorting_direction)
        self.update_browsing_state(
            self.browsing_history.current.with_sorting_direction(self.main_window.sorting_direction)
        )

    def sorting_mode_callback(self):
        logger.info("Sorting Mode Changed", mode=self.main_window.sorting_mode)
        self.update_browsing_state(
            self.browsing_history.current.with_sorting_mode(self.main_window.sorting_mode)
        )

    def thumb_size_callback(self, size: int):
        """Perform actions needed when the thumbnail size selection is changed."""
        spacing_divisor: int = 10
        min_spacing: int = 12

        self.update_thumbs()
        blank_icon: QIcon = QIcon()
        for it in self.item_thumbs:
            it.thumb_button.setIcon(blank_icon)
            it.resize(self.main_window.thumb_size, self.main_window.thumb_size)
            it.thumb_size = (self.main_window.thumb_size, self.main_window.thumb_size)
            it.setFixedSize(self.main_window.thumb_size, self.main_window.thumb_size)
            it.thumb_button.thumb_size = (self.main_window.thumb_size, self.main_window.thumb_size)
            it.set_filename_visibility(it.show_filename_label)
        self.main_window.thumb_layout.setSpacing(
            min(self.main_window.thumb_size // spacing_divisor, min_spacing)
        )

    def mouse_navigation(self, event: QMouseEvent):
        # print(event.button())
        if event.button() == Qt.MouseButton.ForwardButton:
            self.navigation_callback(1)
        elif event.button() == Qt.MouseButton.BackButton:
            self.navigation_callback(-1)

    def page_move(self, value: int, absolute=False) -> None:
        logger.info("page_move", value=value, absolute=absolute)

        if not absolute:
            value += self.browsing_history.current.page_index

        self.browsing_history.push(
            self.browsing_history.current.with_page_index(clamp(value, 0, self.pages_count - 1))
        )

        # TODO: Re-allow selecting entries across multiple pages at once.
        # This works fine with additive selection but becomes a nightmare with bridging.

        self.update_browsing_state()

    def navigation_callback(self, delta: int) -> None:
        """Callback for the Forwads and Backwards Navigation Buttons next to the search bar."""
        logger.info(
            "navigation_callback",
            delta=delta,
        )

        self.browsing_history.move(delta)

        self.update_browsing_state()

    def remove_grid_item(self, grid_idx: int):
        self.frame_content[grid_idx] = None
        self.item_thumbs[grid_idx].hide()

    def _update_thumb_count(self):
        missing_count = max(0, self.settings.page_size - len(self.item_thumbs))
        layout = self.main_window.thumb_layout
        for _ in range(missing_count):
            item_thumb = ItemThumb(
                None,
                self.lib,
                self,
                (self.main_window.thumb_size, self.main_window.thumb_size),
                self.settings.show_filenames_in_grid,
            )

            layout.addWidget(item_thumb)
            self.item_thumbs.append(item_thumb)

    def copy_fields_action_callback(self):
        if len(self.selected) > 0:
            entry = self.lib.get_entry_full(self.selected[0])
            if entry:
                self.copy_buffer["fields"] = entry.fields
                self.copy_buffer["tags"] = [tag.id for tag in entry.tags]
        self.set_clipboard_menu_viability()

    def paste_fields_action_callback(self):
        for id in self.selected:
            entry = self.lib.get_entry_full(id, with_fields=True, with_tags=False)
            if not entry:
                continue
            existing_fields = entry.fields
            for field in self.copy_buffer["fields"]:
                exists = False
                for e in existing_fields:
                    if field.type_key == e.type_key and field.value == e.value:
                        exists = True
                if not exists:
                    self.lib.add_field_to_entry(id, field_id=field.type_key, value=field.value)
            self.lib.add_tags_to_entries(id, self.copy_buffer["tags"])
        if len(self.selected) > 1:
            if TAG_ARCHIVED in self.copy_buffer["tags"]:
                self.update_badges({BadgeType.ARCHIVED: True}, origin_id=0, add_tags=False)
            if TAG_FAVORITE in self.copy_buffer["tags"]:
                self.update_badges({BadgeType.FAVORITE: True}, origin_id=0, add_tags=False)
        else:
            self.main_window.preview_panel.update_widgets()

    def toggle_item_selection(self, item_id: int, append: bool, bridge: bool):
        """Toggle the selection of an item in the Thumbnail Grid.

        If an item is not selected, this selects it. If an item is already selected, this will
        deselect it as long as append and bridge are False.

        Args:
            item_id(int): The ID of the item/entry to select.
            append(bool): Whether or not to add this item to the previous selection
                or to restart the selection with this item.
                Setting to True acts like "Ctrl + Click" selecting.
            bridge(bool): Whether or not to select items in the visual range of the last item
                selected and this current item.
                Setting to True acts like "Shift + Click" selecting.
        """
        logger.info("[QtDriver] Selecting Items:", item_id=item_id, append=append, bridge=bridge)

        if append:
            if item_id not in self.selected:
                self.selected.append(item_id)
                for it in self.item_thumbs:
                    if it.item_id == item_id:
                        it.thumb_button.set_selected(True)
            else:
                self.selected.remove(item_id)
                for it in self.item_thumbs:
                    if it.item_id == item_id:
                        it.thumb_button.set_selected(False)

        #  TODO: Allow bridge selecting across pages.
        elif bridge and self.selected:
            last_index = -1
            current_index = -1
            try:
                contents = self.frame_content
                last_index = self.frame_content.index(self.selected[-1])
                current_index = self.frame_content.index(item_id)
                index_range: list = contents[
                    min(last_index, current_index) : max(last_index, current_index) + 1
                ]

                # Preserve bridge direction for correct appending order.
                if last_index < current_index:
                    index_range.reverse()
                for entry_id in index_range:
                    for it in self.item_thumbs:
                        if it.item_id == entry_id:
                            it.thumb_button.set_selected(True)
                            if entry_id not in self.selected:
                                self.selected.append(entry_id)
            except Exception as e:
                # TODO: Allow bridge selecting across pages.
                logger.error(
                    "[QtDriver] Previous selected item not on current page!",
                    error=e,
                    item_id=item_id,
                    current_index=current_index,
                    last_index=last_index,
                )

        else:
            self.selected.clear()
            self.selected.append(item_id)
        for it in self.item_thumbs:
            if it.item_id in self.selected:
                it.thumb_button.set_selected(True)
            else:
                it.thumb_button.set_selected(False)

        self.set_clipboard_menu_viability()
        self.set_select_actions_visibility()

        self.main_window.preview_panel.update_widgets()

    def set_clipboard_menu_viability(self):
        if len(self.selected) == 1:
            self.main_window.menu_bar.copy_fields_action.setEnabled(True)
        else:
            self.main_window.menu_bar.copy_fields_action.setEnabled(False)
        if self.selected and (self.copy_buffer["fields"] or self.copy_buffer["tags"]):
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

        if self.selected:
            self.main_window.menu_bar.add_tag_to_selected_action.setEnabled(True)
            self.main_window.menu_bar.clear_select_action.setEnabled(True)
            self.main_window.menu_bar.delete_file_action.setEnabled(True)
        else:
            self.main_window.menu_bar.add_tag_to_selected_action.setEnabled(False)
            self.main_window.menu_bar.clear_select_action.setEnabled(False)
            self.main_window.menu_bar.delete_file_action.setEnabled(False)

    def update_completions_list(self, text: str) -> None:
        matches = re.search(
            r"((?:.* )?)(mediatype|filetype|path|tag|tag_id):(\"?[A-Za-z0-9\ \t]+\"?)?", text
        )

        completion_list: list[str] = []
        if len(text) < 3:
            completion_list = [
                "mediatype:",
                "filetype:",
                "path:",
                "tag:",
                "tag_id:",
                "special:untagged",
            ]
            self.main_window.search_field_completion_list.setStringList(completion_list)

        if not matches:
            return

        query_type: str
        query_value: str | None
        prefix, query_type, query_value = matches.groups()

        if not query_value:
            return

        if query_type == "tag":
            completion_list = list(map(lambda x: prefix + "tag:" + x.name, self.lib.tags))
        elif query_type == "tag_id":
            completion_list = list(map(lambda x: prefix + "tag_id:" + str(x.id), self.lib.tags))
        elif query_type == "path":
            completion_list = list(
                map(lambda x: prefix + "path:" + x, self.lib.get_paths(limit=100))
            )
        elif query_type == "mediatype":
            single_word_completions = map(
                lambda x: prefix + "mediatype:" + x.name,
                filter(lambda y: " " not in y.name, MediaCategories.ALL_CATEGORIES),
            )
            single_word_completions_quoted = map(
                lambda x: prefix + 'mediatype:"' + x.name + '"',
                filter(lambda y: " " not in y.name, MediaCategories.ALL_CATEGORIES),
            )
            multi_word_completions = map(
                lambda x: prefix + 'mediatype:"' + x.name + '"',
                filter(lambda y: " " in y.name, MediaCategories.ALL_CATEGORIES),
            )

            all_completions = [
                single_word_completions,
                single_word_completions_quoted,
                multi_word_completions,
            ]
            completion_list = [j for i in all_completions for j in i]
        elif query_type == "filetype":
            extensions_list: set[str] = set()
            for media_cat in MediaCategories.ALL_CATEGORIES:
                extensions_list = extensions_list | media_cat.extensions
            completion_list = list(
                map(lambda x: prefix + "filetype:" + x.replace(".", ""), extensions_list)
            )

        update_completion_list: bool = (
            completion_list != self.main_window.search_field_completion_list.stringList()
            or self.main_window.search_field_completion_list == []
        )
        if update_completion_list:
            self.main_window.search_field_completion_list.setStringList(completion_list)

    def update_thumbs(self):
        """Update search thumbnails."""
        self._update_thumb_count()
        # logger.info(f'Current Page: {self.cur_page_idx}, Stack Length:{len(self.nav_stack)}')
        with self.thumb_job_queue.mutex:
            # Cancels all thumb jobs waiting to be started
            self.thumb_job_queue.queue.clear()
            self.thumb_job_queue.all_tasks_done.notify_all()
            self.thumb_job_queue.not_full.notify_all()
            # Stops in-progress jobs from finishing
            ItemThumb.update_cutoff = time.time()

        ratio: float = self.main_window.devicePixelRatio()
        base_size: tuple[int, int] = (self.main_window.thumb_size, self.main_window.thumb_size)

        self.main_window.thumb_layout.update()
        self.main_window.update()

        is_grid_thumb = True
        logger.info("[QtDriver] Loading Entries...")
        # TODO: The full entries with joins don't need to be grabbed here.
        # Use a method that only selects the frame content but doesn't include the joins.
        entries: list[Entry] = list(self.lib.get_entries_full(self.frame_content))
        logger.info("[QtDriver] Building Filenames...")
        filenames: list[Path] = [self.lib.library_dir / e.path for e in entries]
        logger.info("[QtDriver] Done! Processing ItemThumbs...")
        for index, item_thumb in enumerate(self.item_thumbs, start=0):
            entry = None
            try:
                entry = entries[index]
            except IndexError:
                item_thumb.hide()
                continue
            if not entry:
                continue

            with catch_warnings(record=True):
                item_thumb.delete_action.triggered.disconnect()

            item_thumb.set_mode(ItemType.ENTRY)
            item_thumb.set_item_id(entry.id)
            item_thumb.show()
            is_loading = True
            self.thumb_job_queue.put(
                (
                    item_thumb.renderer.render,
                    (sys.float_info.max, "", base_size, ratio, is_loading, is_grid_thumb),
                )
            )

        # Show rendered thumbnails
        for index, item_thumb in enumerate(self.item_thumbs, start=0):
            entry = None
            try:
                entry = entries[index]
            except IndexError:
                item_thumb.hide()
                continue
            if not entry:
                continue

            is_loading = False
            self.thumb_job_queue.put(
                (
                    item_thumb.renderer.render,
                    (time.time(), filenames[index], base_size, ratio, is_loading, is_grid_thumb),
                )
            )
            item_thumb.assign_badge(BadgeType.ARCHIVED, entry.is_archived)
            item_thumb.assign_badge(BadgeType.FAVORITE, entry.is_favorite)
            item_thumb.update_clickable(
                clickable=(
                    lambda checked=False, item_id=entry.id: self.toggle_item_selection(
                        item_id,
                        append=(
                            QGuiApplication.keyboardModifiers()
                            == Qt.KeyboardModifier.ControlModifier
                        ),
                        bridge=(
                            QGuiApplication.keyboardModifiers() == Qt.KeyboardModifier.ShiftModifier
                        ),
                    )
                )
            )
            item_thumb.delete_action.triggered.connect(
                lambda checked=False, f=filenames[index], e_id=entry.id: self.delete_files_callback(
                    f, e_id
                )
            )

            # Restore Selected Borders
            is_selected = item_thumb.item_id in self.selected
            item_thumb.thumb_button.set_selected(is_selected)

    def update_badges(self, badge_values: dict[BadgeType, bool], origin_id: int, add_tags=True):
        """Update the tag badges for item_thumbs.

        Args:
            badge_values(dict[BadgeType, bool]): The BadgeType and associated viability state.
            origin_id(int): The ID of the item_thumb calling this method. If the ID is found as a
                part of the current selection, or if the ID is 0, the the entire current selection
                will be updated. Otherwise, only item_thumbs with that ID will be updated.
            add_tags(bool): Flag determining if tags associated with the badges need to be added to
                the items. Defaults to True.
        """
        item_ids = self.selected if (not origin_id or origin_id in self.selected) else [origin_id]
        pending_entries: dict[BadgeType, list[int]] = {}

        logger.info(
            "[QtDriver][update_badges] Updating ItemThumb badges",
            badge_values=badge_values,
            origin_id=origin_id,
            add_tags=add_tags,
        )
        for it in self.item_thumbs:
            if it.item_id in item_ids:
                for badge_type, value in badge_values.items():
                    if add_tags:
                        if not pending_entries.get(badge_type):
                            pending_entries[badge_type] = []
                        pending_entries[badge_type].append(it.item_id)
                        it.toggle_item_tag(it.item_id, value, BADGE_TAGS[badge_type])
                    it.assign_badge(badge_type, value)

        if not add_tags:
            return

        logger.info(
            "[QtDriver][update_badges] Adding tags to updated entries",
            pending_entries=pending_entries,
        )
        for badge_type, value in badge_values.items():
            if value:
                self.lib.add_tags_to_entries(
                    pending_entries.get(badge_type, []), BADGE_TAGS[badge_type]
                )
            else:
                self.lib.remove_tags_from_entries(
                    pending_entries.get(badge_type, []), BADGE_TAGS[badge_type]
                )

    def update_browsing_state(self, state: BrowsingState | None = None) -> None:
        """Navigates to a new BrowsingState when state is given, otherwise updates the results."""
        if not self.lib.library_dir:
            logger.info("Library not loaded")
            return
        assert self.lib.engine

        if state:
            self.browsing_history.push(state)

        self.main_window.search_field.setText(self.browsing_history.current.query or "")

        # inform user about running search
        self.main_window.status_bar.showMessage(Translations["status.library_search_query"])
        self.main_window.status_bar.repaint()

        # search the library
        start_time = time.time()
        results = self.lib.search_library(self.browsing_history.current, self.settings.page_size)
        logger.info("items to render", count=len(results))
        end_time = time.time()

        # inform user about completed search
        self.main_window.status_bar.showMessage(
            Translations.format(
                "status.results_found",
                count=results.total_count,
                time_span=format_timespan(end_time - start_time),
            )
        )

        # update page content
        self.frame_content = [item.id for item in results.items]
        self.update_thumbs()

        # update pagination
        self.pages_count = math.ceil(results.total_count / self.settings.page_size)
        self.main_window.pagination.update_buttons(
            self.pages_count, self.browsing_history.current.page_index, emit=False
        )

    def remove_recent_library(self, item_key: str):
        self.cached_values.beginGroup(SettingItems.LIBS_LIST)
        self.cached_values.remove(item_key)
        self.cached_values.endGroup()
        self.cached_values.sync()

    def update_libs_list(self, path: Path | str):
        """Add library to list in SettingItems.LIBS_LIST."""
        item_limit: int = 10
        path = Path(path)

        self.cached_values.beginGroup(SettingItems.LIBS_LIST)

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
        self.cached_values.beginGroup(SettingItems.LIBS_LIST)
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
        settings = self.cached_values
        settings.beginGroup(SettingItems.LIBS_LIST)
        self.cached_values.remove("")
        self.cached_values.endGroup()
        self.cached_values.sync()
        self.update_recent_lib_menu()

    def open_settings_modal(self):
        SettingsPanel.build_modal(self).show()

    def open_library(self, path: Path) -> None:
        """Open a TagStudio library."""
        library_dir_display = (
            path if self.settings.show_filepath == ShowFilepathOption.SHOW_FULL_PATHS else path.name
        )
        message = Translations.format("splash.opening_library", library_path=library_dir_display)
        self.main_window.landing_widget.set_status_label(message)
        self.main_window.status_bar.showMessage(message, 3)
        self.main_window.repaint()

        if self.lib.library_dir:
            self.close_library()

        open_status: LibraryStatus | None = None
        try:
            open_status = self.lib.open_library(path)
        except ValueError as e:
            logger.warning(e)
            open_status = LibraryStatus(
                success=False,
                library_path=path,
                message=Translations["menu.file.missing_library.title"],
                msg_description=Translations.format(
                    "menu.file.missing_library.message", library=library_dir_display
                ),
            )
        except Exception as e:
            logger.error(e)
            open_status = LibraryStatus(
                success=False, library_path=path, message=type(e).__name__, msg_description=str(e)
            )

        # Migration is required
        if open_status.json_migration_req:
            self.migration_modal = JsonMigrationModal(path)
            self.migration_modal.migration_finished.connect(
                lambda: self._init_library(path, self.lib.open_library(path))
            )
            self.main_window.landing_widget.set_status_label("")
            self.migration_modal.paged_panel.show()
        else:
            self._init_library(path, open_status)

    def _init_library(self, path: Path, open_status: LibraryStatus):
        if not open_status.success:
            self.show_error_message(
                error_name=open_status.message
                or Translations["window.message.error_opening_library"],
                error_desc=open_status.msg_description,
            )
            return open_status

        self.init_workers()

        self.__reset_navigation()

        # TODO - make this call optional
        if self.lib.entries_count < 10000:
            self.add_new_files_callback()

        if self.settings.show_filepath == ShowFilepathOption.SHOW_FULL_PATHS:
            library_dir_display = self.lib.library_dir
        else:
            library_dir_display = self.lib.library_dir.name

        self.update_libs_list(path)
        self.main_window.setWindowTitle(
            Translations.format(
                "app.title",
                base_title=self.base_title,
                library_dir=library_dir_display,
            )
        )
        self.main_window.setAcceptDrops(True)

        self.init_file_extension_manager()

        self.selected.clear()
        self.set_select_actions_visibility()
        self.main_window.menu_bar.save_library_backup_action.setEnabled(True)
        self.main_window.menu_bar.close_library_action.setEnabled(True)
        self.main_window.menu_bar.refresh_dir_action.setEnabled(True)
        self.main_window.menu_bar.tag_manager_action.setEnabled(True)
        self.main_window.menu_bar.color_manager_action.setEnabled(True)
        self.main_window.menu_bar.manage_file_ext_action.setEnabled(True)
        self.main_window.menu_bar.new_tag_action.setEnabled(True)
        self.main_window.menu_bar.fix_unlinked_entries_action.setEnabled(True)
        self.main_window.menu_bar.fix_dupe_files_action.setEnabled(True)
        self.main_window.menu_bar.clear_thumb_cache_action.setEnabled(True)
        self.main_window.menu_bar.folders_to_tags_action.setEnabled(True)

        self.main_window.preview_panel.update_widgets()

        # page (re)rendering, extract eventually
        self.update_browsing_state()

        self.main_window.toggle_landing_page(enabled=False)
        return open_status

    def drop_event(self, event: QDropEvent):
        if event.source() is self:
            return

        if not event.mimeData().hasUrls():
            return

        urls = event.mimeData().urls()
        logger.info("New items dragged in", urls=urls)
        drop_import = DropImportModal(self)
        drop_import.import_urls(urls)

    def drag_enter_event(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def drag_move_event(self, event: QDragMoveEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
