# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

# SIGTERM handling based on the implementation by Virgil Dupras for dupeGuru:
# https://github.com/arsenetar/dupeguru/blob/master/run.py#L71

"""A Qt driver for TagStudio."""

import ctypes
import dataclasses
import math
import os
import re
import sys
import time
import webbrowser
from pathlib import Path
from queue import Queue

# this import has side-effect of import PySide resources
import src.qt.resources_rc  # noqa: F401
import structlog
from humanfriendly import format_timespan
from PySide6 import QtCore
from PySide6.QtCore import QObject, QSettings, Qt, QThread, QThreadPool, QTimer, Signal
from PySide6.QtGui import (
    QAction,
    QColor,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QFontDatabase,
    QGuiApplication,
    QIcon,
    QMouseEvent,
    QPixmap,
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QLineEdit,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplashScreen,
    QWidget,
)
from src.core.constants import (
    TAG_ARCHIVED,
    TAG_FAVORITE,
    VERSION,
    VERSION_BRANCH,
)
from src.core.driver import DriverMixin
from src.core.enums import LibraryPrefs, MacroID, SettingItems
from src.core.library.alchemy import Library
from src.core.library.alchemy.enums import (
    FieldTypeEnum,
    FilterState,
    ItemType,
    SortingModeEnum,
)
from src.core.library.alchemy.fields import _FieldID
from src.core.library.alchemy.library import Entry, LibraryStatus
from src.core.media_types import MediaCategories
from src.core.ts_core import TagStudioCore
from src.core.utils.refresh_dir import RefreshDirTracker
from src.core.utils.web import strip_web_protocol
from src.qt.flowlayout import FlowLayout
from src.qt.helpers.custom_runnable import CustomRunnable
from src.qt.helpers.function_iterator import FunctionIterator
from src.qt.main_window import Ui_MainWindow
from src.qt.modals.build_tag import BuildTagPanel
from src.qt.modals.drop_import import DropImportModal
from src.qt.modals.file_extension import FileExtensionModal
from src.qt.modals.fix_dupes import FixDupeFilesModal
from src.qt.modals.fix_unlinked import FixUnlinkedEntriesModal
from src.qt.modals.folders_to_tags import FoldersToTagsModal
from src.qt.modals.tag_database import TagDatabasePanel
from src.qt.resource_manager import ResourceManager
from src.qt.translations import Translations
from src.qt.widgets.item_thumb import BadgeType, ItemThumb
from src.qt.widgets.migration_modal import JsonMigrationModal
from src.qt.widgets.panel import PanelModal
from src.qt.widgets.preview_panel import PreviewPanel
from src.qt.widgets.progress import ProgressWidget
from src.qt.widgets.thumb_renderer import ThumbRenderer

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


class QtDriver(DriverMixin, QObject):
    """A Qt GUI frontend driver for TagStudio."""

    SIGTERM = Signal()

    preview_panel: PreviewPanel
    lib: Library

    def __init__(self, backend, args):
        super().__init__()
        # prevent recursive badges update when multiple items selected
        self.badge_update_lock = False
        self.lib = backend.Library()
        self.rm: ResourceManager = ResourceManager()
        self.args = args
        self.filter = FilterState.show_all()
        self.frame_content: list[int] = []  # List of Entry IDs on the current page
        self.pages_count = 0

        self.scrollbar_pos = 0
        self.thumb_size = 128
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

        if self.args.config_file:
            path = Path(self.args.config_file)
            if not path.exists():
                logger.warning("Config File does not exist creating", path=path)
            logger.info("Using Config File", path=path)
            self.settings = QSettings(str(path), QSettings.Format.IniFormat)
        else:
            self.settings = QSettings(
                QSettings.Format.IniFormat,
                QSettings.Scope.UserScope,
                "TagStudio",
                "TagStudio",
            )
            logger.info(
                "Config File not specified, using default one",
                filename=self.settings.fileName(),
            )

    def init_workers(self):
        """Init workers for rendering thumbnails."""
        if not self.thumb_threads:
            max_threads = os.cpu_count()
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
        _ = QUiLoader()
        if os.name == "nt":
            sys.argv += ["-platform", "windows:darkmode=2"]

        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        # pal: QPalette = app.palette()
        # pal.setColor(QPalette.ColorGroup.Active,
        # 			 QPalette.ColorRole.Highlight, QColor('#6E4BCE'))
        # pal.setColor(QPalette.ColorGroup.Normal,
        # 			 QPalette.ColorRole.Window, QColor('#110F1B'))
        # app.setPalette(pal)
        # home_path = Path(__file__).parent / "ui/home.ui"
        icon_path = Path(__file__).parents[2] / "resources/icon.png"

        # Handle OS signals
        self.setup_signals()
        # allow to process input from console, eg. SIGTERM
        timer = QTimer()
        timer.start(500)
        timer.timeout.connect(lambda: None)

        # self.main_window = loader.load(home_path)
        self.main_window = Ui_MainWindow(self)
        self.main_window.setWindowTitle(self.base_title)
        self.main_window.mousePressEvent = self.mouse_navigation  # type: ignore[method-assign]
        self.main_window.dragEnterEvent = self.drag_enter_event  # type: ignore[method-assign]
        self.main_window.dragMoveEvent = self.drag_move_event  # type: ignore[method-assign]
        self.main_window.dropEvent = self.drop_event  # type: ignore[method-assign]

        splash_pixmap = QPixmap(":/images/splash.png")
        splash_pixmap.setDevicePixelRatio(self.main_window.devicePixelRatio())
        splash_pixmap = splash_pixmap.scaledToWidth(
            math.floor(
                min(
                    (
                        QGuiApplication.primaryScreen().geometry().width()
                        * self.main_window.devicePixelRatio()
                    )
                    / 4,
                    splash_pixmap.width(),
                )
            ),
            Qt.TransformationMode.SmoothTransformation,
        )
        self.splash = QSplashScreen(splash_pixmap, Qt.WindowType.WindowStaysOnTopHint)
        # self.splash.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.splash.show()

        if os.name == "nt":
            appid = "cyanvoxel.tagstudio.9"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)  # type: ignore[attr-defined,unused-ignore]

        if sys.platform != "darwin":
            icon = QIcon()
            icon.addFile(str(icon_path))
            app.setWindowIcon(icon)

        menu_bar = QMenuBar(self.main_window)
        self.main_window.setMenuBar(menu_bar)
        menu_bar.setNativeMenuBar(True)

        file_menu = QMenu(menu_bar)
        Translations.translate_qobject(file_menu, "menu.file")
        edit_menu = QMenu(menu_bar)
        Translations.translate_qobject(edit_menu, "generic.edit_alt")
        view_menu = QMenu(menu_bar)
        Translations.translate_qobject(view_menu, "menu.view")
        tools_menu = QMenu(menu_bar)
        Translations.translate_qobject(tools_menu, "menu.tools")
        macros_menu = QMenu(menu_bar)
        Translations.translate_qobject(macros_menu, "menu.macros")
        help_menu = QMenu(menu_bar)
        Translations.translate_qobject(help_menu, "menu.help")

        # File Menu ============================================================
        open_library_action = QAction(menu_bar)
        Translations.translate_qobject(open_library_action, "menu.file.open_create_library")
        open_library_action.triggered.connect(lambda: self.open_library_from_dialog())
        open_library_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_O,
            )
        )
        open_library_action.setToolTip("Ctrl+O")
        file_menu.addAction(open_library_action)

        self.open_recent_library_menu = QMenu(menu_bar)
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

        save_library_backup_action = QAction(menu_bar)
        Translations.translate_qobject(save_library_backup_action, "menu.file.save_backup")
        save_library_backup_action.triggered.connect(
            lambda: self.callback_library_needed_check(self.backup_library)
        )
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

        add_new_files_action = QAction(menu_bar)
        Translations.translate_qobject(add_new_files_action, "menu.file.refresh_directories")
        add_new_files_action.triggered.connect(
            lambda: self.callback_library_needed_check(self.add_new_files_callback)
        )
        add_new_files_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_R,
            )
        )
        add_new_files_action.setStatusTip("Ctrl+R")
        file_menu.addAction(add_new_files_action)
        file_menu.addSeparator()

        close_library_action = QAction(menu_bar)
        Translations.translate_qobject(close_library_action, "menu.file.close_library")
        close_library_action.triggered.connect(self.close_library)
        file_menu.addAction(close_library_action)
        file_menu.addSeparator()

        # Edit Menu ============================================================
        new_tag_action = QAction(menu_bar)
        Translations.translate_qobject(new_tag_action, "menu.edit.new_tag")
        new_tag_action.triggered.connect(lambda: self.add_tag_action_callback())
        new_tag_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_T,
            )
        )
        new_tag_action.setToolTip("Ctrl+T")
        edit_menu.addAction(new_tag_action)

        edit_menu.addSeparator()

        select_all_action = QAction(menu_bar)
        Translations.translate_qobject(select_all_action, "select.all")
        select_all_action.triggered.connect(self.select_all_action_callback)
        select_all_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_A,
            )
        )
        select_all_action.setToolTip("Ctrl+A")
        edit_menu.addAction(select_all_action)

        clear_select_action = QAction(menu_bar)
        Translations.translate_qobject(clear_select_action, "select.clear")
        clear_select_action.triggered.connect(self.clear_select_action_callback)
        clear_select_action.setShortcut(QtCore.Qt.Key.Key_Escape)
        clear_select_action.setToolTip("Esc")
        edit_menu.addAction(clear_select_action)

        edit_menu.addSeparator()

        manage_file_extensions_action = QAction(menu_bar)
        Translations.translate_qobject(
            manage_file_extensions_action, "menu.edit.manage_file_extensions"
        )
        manage_file_extensions_action.triggered.connect(self.show_file_extension_modal)
        edit_menu.addAction(manage_file_extensions_action)

        tag_database_action = QAction(menu_bar)
        Translations.translate_qobject(tag_database_action, "menu.edit.manage_tags")
        tag_database_action.triggered.connect(lambda: self.show_tag_database())
        edit_menu.addAction(tag_database_action)

        # View Menu ============================================================
        show_libs_list_action = QAction(menu_bar)
        Translations.translate_qobject(show_libs_list_action, "settings.show_recent_libraries")
        show_libs_list_action.setCheckable(True)
        show_libs_list_action.setChecked(
            bool(self.settings.value(SettingItems.WINDOW_SHOW_LIBS, defaultValue=True, type=bool))
        )

        show_filenames_action = QAction(menu_bar)
        Translations.translate_qobject(show_filenames_action, "settings.show_filenames_in_grid")
        show_filenames_action.setCheckable(True)
        show_filenames_action.setChecked(
            bool(self.settings.value(SettingItems.SHOW_FILENAMES, defaultValue=True, type=bool))
        )
        show_filenames_action.triggered.connect(
            lambda checked: (
                self.settings.setValue(SettingItems.SHOW_FILENAMES, checked),
                self.show_grid_filenames(checked),
            )
        )
        view_menu.addAction(show_filenames_action)

        # Tools Menu ===========================================================
        def create_fix_unlinked_entries_modal():
            if not hasattr(self, "unlinked_modal"):
                self.unlinked_modal = FixUnlinkedEntriesModal(self.lib, self)
            self.unlinked_modal.show()

        fix_unlinked_entries_action = QAction(menu_bar)
        Translations.translate_qobject(
            fix_unlinked_entries_action, "menu.tools.fix_unlinked_entries"
        )
        fix_unlinked_entries_action.triggered.connect(create_fix_unlinked_entries_modal)
        tools_menu.addAction(fix_unlinked_entries_action)

        def create_dupe_files_modal():
            if not hasattr(self, "dupe_modal"):
                self.dupe_modal = FixDupeFilesModal(self.lib, self)
            self.dupe_modal.show()

        fix_dupe_files_action = QAction(menu_bar)
        Translations.translate_qobject(fix_dupe_files_action, "menu.tools.fix_duplicate_files")
        fix_dupe_files_action.triggered.connect(create_dupe_files_modal)
        tools_menu.addAction(fix_dupe_files_action)

        # create_collage_action = QAction("Create Collage", menu_bar)
        # create_collage_action.triggered.connect(lambda: self.create_collage())
        # tools_menu.addAction(create_collage_action)

        # Macros Menu ==========================================================
        self.autofill_action = QAction("Autofill", menu_bar)
        self.autofill_action.triggered.connect(
            lambda: (
                self.run_macros(MacroID.AUTOFILL, self.selected),
                self.preview_panel.update_widgets(update_preview=False),
            )
        )
        macros_menu.addAction(self.autofill_action)

        def create_folders_tags_modal():
            if not hasattr(self, "folders_modal"):
                self.folders_modal = FoldersToTagsModal(self.lib, self)
            self.folders_modal.show()

        folders_to_tags_action = QAction(menu_bar)
        Translations.translate_qobject(folders_to_tags_action, "menu.macros.folders_to_tags")
        folders_to_tags_action.triggered.connect(create_folders_tags_modal)
        macros_menu.addAction(folders_to_tags_action)

        # Help Menu ============================================================
        self.repo_action = QAction(menu_bar)
        Translations.translate_qobject(self.repo_action, "help.visit_github")
        self.repo_action.triggered.connect(
            lambda: webbrowser.open("https://github.com/TagStudioDev/TagStudio")
        )
        help_menu.addAction(self.repo_action)
        self.set_macro_menu_viability()

        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(edit_menu)
        menu_bar.addMenu(view_menu)
        menu_bar.addMenu(tools_menu)
        menu_bar.addMenu(macros_menu)
        menu_bar.addMenu(help_menu)

        self.main_window.searchField.textChanged.connect(self.update_completions_list)

        self.preview_panel = PreviewPanel(self.lib, self)
        self.preview_panel.fields.archived_updated.connect(
            lambda hidden: self.update_badges(
                {BadgeType.ARCHIVED: hidden}, origin_id=0, add_tags=False
            )
        )
        self.preview_panel.fields.favorite_updated.connect(
            lambda hidden: self.update_badges(
                {BadgeType.FAVORITE: hidden}, origin_id=0, add_tags=False
            )
        )

        splitter = self.main_window.splitter
        splitter.addWidget(self.preview_panel)

        QFontDatabase.addApplicationFont(
            str(Path(__file__).parents[2] / "resources/qt/fonts/Oxanium-Bold.ttf")
        )

        # TODO this doesn't update when the language is changed
        self.thumb_sizes: list[tuple[str, int]] = [
            (Translations["home.thumbnail_size.extra_large"], 256),
            (Translations["home.thumbnail_size.large"], 192),
            (Translations["home.thumbnail_size.medium"], 128),
            (Translations["home.thumbnail_size.small"], 96),
            (Translations["home.thumbnail_size.mini"], 76),
        ]
        self.item_thumbs: list[ItemThumb] = []
        self.thumb_renderers: list[ThumbRenderer] = []
        self.filter = FilterState.show_all()
        self.init_library_window()
        self.migration_modal: JsonMigrationModal = None

        path_result = self.evaluate_path(str(self.args.open).lstrip().rstrip())
        # check status of library path evaluating
        if path_result.success and path_result.library_path:
            self.splash.showMessage(
                Translations.translate_formatted(
                    "splash.opening_library", library_path=path_result.library_path
                ),
                int(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter),
                QColor("#9782ff"),
            )
            self.open_library(path_result.library_path)

        app.exec()
        self.shutdown()

    def show_error_message(self, message: str):
        self.main_window.statusbar.showMessage(message, Qt.AlignmentFlag.AlignLeft)
        self.main_window.landing_widget.set_status_label(message)
        self.main_window.setWindowTitle(message)

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setText(message)
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

        # Search Button
        search_button: QPushButton = self.main_window.searchButton
        search_button.clicked.connect(
            lambda: self.filter_items(
                FilterState.from_search_query(self.main_window.searchField.text())
                .with_sorting_mode(self.sorting_mode)
                .with_sorting_direction(self.sorting_direction)
            )
        )
        # Search Field
        search_field: QLineEdit = self.main_window.searchField
        search_field.returnPressed.connect(
            lambda: self.filter_items(
                FilterState.from_search_query(self.main_window.searchField.text())
                .with_sorting_mode(self.sorting_mode)
                .with_sorting_direction(self.sorting_direction)
            )
        )
        # Sorting Dropdowns
        sort_mode_dropdown: QComboBox = self.main_window.sorting_mode_combobox
        for sort_mode in SortingModeEnum:
            sort_mode_dropdown.addItem(Translations[sort_mode.value], sort_mode)
        sort_mode_dropdown.setCurrentIndex(
            list(SortingModeEnum).index(self.filter.sorting_mode)
        )  # set according to self.filter
        sort_mode_dropdown.currentIndexChanged.connect(self.sorting_mode_callback)

        sort_dir_dropdown: QComboBox = self.main_window.sorting_direction_combobox
        sort_dir_dropdown.addItem("Ascending", userData=True)
        sort_dir_dropdown.addItem("Descending", userData=False)
        Translations.translate_with_setter(
            lambda text: sort_dir_dropdown.setItemText(0, text), "sorting.direction.ascending"
        )
        Translations.translate_with_setter(
            lambda text: sort_dir_dropdown.setItemText(1, text), "sorting.direction.descending"
        )
        sort_dir_dropdown.setCurrentIndex(0)  # Default: Ascending
        sort_dir_dropdown.currentIndexChanged.connect(self.sorting_direction_callback)

        # Thumbnail Size ComboBox
        thumb_size_combobox: QComboBox = self.main_window.thumb_size_combobox
        for size in self.thumb_sizes:
            thumb_size_combobox.addItem(size[0])
        thumb_size_combobox.setCurrentIndex(2)  # Default: Medium
        thumb_size_combobox.currentIndexChanged.connect(
            lambda: self.thumb_size_callback(thumb_size_combobox.currentIndex())
        )
        self._init_thumb_grid()

        back_button: QPushButton = self.main_window.backButton
        back_button.clicked.connect(lambda: self.page_move(-1))
        forward_button: QPushButton = self.main_window.forwardButton
        forward_button.clicked.connect(lambda: self.page_move(1))

        # NOTE: Putting this early will result in a white non-responsive
        # window until everything is loaded. Consider adding a splash screen
        # or implementing some clever loading tricks.
        self.main_window.show()
        self.main_window.activateWindow()
        self.main_window.toggle_landing_page(enabled=True)

        self.main_window.pagination.index.connect(lambda i: self.page_move(page_id=i))

        self.splash.finish(self.main_window)

    def show_grid_filenames(self, value: bool):
        for thumb in self.item_thumbs:
            thumb.set_filename_visibility(value)

    def callback_library_needed_check(self, func):
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
        self.main_window.statusbar.showMessage(Translations["status.library_closing"])
        start_time = time.time()

        self.settings.setValue(SettingItems.LAST_LIBRARY, str(self.lib.library_dir))
        self.settings.sync()

        self.preview_panel.update_widgets()
        self.main_window.searchField.setText("")
        self.filter = FilterState.show_all()

        self.lib.close()

        self.thumb_job_queue.queue.clear()
        if is_shutdown:
            # no need to do other things on shutdown
            return

        self.main_window.setWindowTitle(self.base_title)

        self.selected = []
        self.frame_content = []
        [x.set_mode(None) for x in self.item_thumbs]

        self.preview_panel.update_widgets()
        self.main_window.toggle_landing_page(enabled=True)

        self.main_window.pagination.setHidden(True)

        end_time = time.time()
        self.main_window.statusbar.showMessage(
            Translations.translate_formatted(
                "status.library_closed", time_span=format_timespan(end_time - start_time)
            )
        )

    def backup_library(self):
        logger.info("Backing Up Library...")
        self.main_window.statusbar.showMessage(Translations["status.library_backup_in_progress"])
        start_time = time.time()
        target_path = self.lib.save_library_backup_to_disk()
        end_time = time.time()
        self.main_window.statusbar.showMessage(
            Translations.translate_formatted(
                "status.library_backup_success",
                path=target_path,
                time_span=format_timespan(end_time - start_time),
            )
        )

    def add_tag_action_callback(self):
        self.modal = PanelModal(
            BuildTagPanel(self.lib),
            has_save=True,
        )
        Translations.translate_with_setter(self.modal.setTitle, "tag.new")
        Translations.translate_with_setter(self.modal.setWindowTitle, "tag.add")

        panel: BuildTagPanel = self.modal.widget
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
            if item.mode and item.item_id not in self.selected:
                self.selected.append(item.item_id)
                item.thumb_button.set_selected(True)

        self.set_macro_menu_viability()
        self.preview_panel.update_widgets(update_preview=False)

    def clear_select_action_callback(self):
        self.selected.clear()
        for item in self.item_thumbs:
            item.thumb_button.set_selected(False)

        self.set_macro_menu_viability()
        self.preview_panel.update_widgets()

    def show_tag_database(self):
        self.modal = PanelModal(
            widget=TagDatabasePanel(self.lib),
            done_callback=lambda: self.preview_panel.update_widgets(update_preview=False),
            has_save=False,
        )
        Translations.translate_with_setter(self.modal.setTitle, "tag_manager.title")
        Translations.translate_with_setter(self.modal.setWindowTitle, "tag_manager.title")
        self.modal.show()

    def show_file_extension_modal(self):
        panel = FileExtensionModal(self.lib)
        self.modal = PanelModal(
            panel,
            has_save=True,
        )
        Translations.translate_with_setter(self.modal.setTitle, "ignore_list.title")
        Translations.translate_with_setter(self.modal.setWindowTitle, "ignore_list.title")

        self.modal.saved.connect(lambda: (panel.save(), self.filter_items()))
        self.modal.show()

    def add_new_files_callback(self):
        """Run when user initiates adding new files to the Library."""
        tracker = RefreshDirTracker(self.lib)

        pw = ProgressWidget(
            cancel_button_text=None,
            minimum=0,
            maximum=0,
        )
        Translations.translate_with_setter(pw.setWindowTitle, "library.refresh.title")
        Translations.translate_with_setter(pw.update_label, "library.refresh.scanning_preparing")

        pw.show()

        iterator = FunctionIterator(lambda: tracker.refresh_dir(self.lib.library_dir))
        iterator.value.connect(
            lambda x: (
                pw.update_progress(x + 1),
                pw.update_label(
                    Translations.translate_formatted(
                        "library.refresh.scanning.plural"
                        if x + 1 != 1
                        else "library.refresh.scanning.singular",
                        searched_count=x + 1,
                        found_count=tracker.files_count,
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
            maximum=files_count,
        )
        Translations.translate_with_setter(pw.setWindowTitle, "macros.running.dialog.title")
        Translations.translate_with_setter(
            pw.update_label, "macros.running.dialog.new_entries", count=1, total=files_count
        )
        pw.show()

        iterator.value.connect(
            lambda x: (
                pw.update_progress(x + 1),
                pw.update_label(
                    Translations.translate_formatted(
                        "macros.running.dialog.new_entries", count=x + 1, total=files_count
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
                files_count and self.filter_items(),
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

    @property
    def sorting_direction(self) -> bool:
        """Whether to Sort the results in ascending order."""
        return self.main_window.sorting_direction_combobox.currentData()

    def sorting_direction_callback(self):
        logger.info("Sorting Direction Changed", ascending=self.sorting_direction)
        self.filter_items()

    @property
    def sorting_mode(self) -> SortingModeEnum:
        """What to sort by."""
        return self.main_window.sorting_mode_combobox.currentData()

    def sorting_mode_callback(self):
        logger.info("Sorting Mode Changed", mode=self.sorting_mode)
        self.filter_items()

    def thumb_size_callback(self, index: int):
        """Perform actions needed when the thumbnail size selection is changed.

        Args:
            index (int): The index of the item_thumbs/ComboBox list to use.
        """
        spacing_divisor: int = 10
        min_spacing: int = 12
        # Index 2 is the default (Medium)
        if index < len(self.thumb_sizes) and index >= 0:
            self.thumb_size = self.thumb_sizes[index][1]
        else:
            logger.error(f"ERROR: Invalid thumbnail size index ({index}). Defaulting to 128px.")
            self.thumb_size = 128

        self.update_thumbs()
        blank_icon: QIcon = QIcon()
        for it in self.item_thumbs:
            it.thumb_button.setIcon(blank_icon)
            it.resize(self.thumb_size, self.thumb_size)
            it.thumb_size = (self.thumb_size, self.thumb_size)
            it.setFixedSize(self.thumb_size, self.thumb_size)
            it.thumb_button.thumb_size = (self.thumb_size, self.thumb_size)
            it.set_filename_visibility(it.show_filename_label)
        self.flow_container.layout().setSpacing(
            min(self.thumb_size // spacing_divisor, min_spacing)
        )

    def mouse_navigation(self, event: QMouseEvent):
        # print(event.button())
        if event.button() == Qt.MouseButton.ForwardButton:
            self.page_move(1)
        elif event.button() == Qt.MouseButton.BackButton:
            self.page_move(-1)

    def page_move(self, delta: int = None, page_id: int = None) -> None:
        """Navigate a step further into the navigation stack."""
        logger.info(
            "page_move",
            delta=delta,
            page_id=page_id,
        )

        # Ex. User visits | A ->[B]     |
        #                 | A    B ->[C]|
        #                 | A   [B]<- C |
        #                 |[A]<- B    C |  Previous routes still exist
        #                 | A ->[D]     |  Stack is cut from [:A] on new route

        # sb: QScrollArea = self.main_window.scrollArea
        # sb_pos = sb.verticalScrollBar().value()

        page_index = page_id if page_id is not None else self.filter.page_index + delta
        page_index = max(0, min(page_index, self.pages_count - 1))

        self.filter.page_index = page_index
        # TODO: Re-allow selecting entries across multiple pages at once.
        # This works fine with additive selection but becomes a nightmare with bridging.
        self.filter_items()

    def remove_grid_item(self, grid_idx: int):
        self.frame_content[grid_idx] = None
        self.item_thumbs[grid_idx].hide()

    def _init_thumb_grid(self):
        layout = FlowLayout()
        layout.enable_grid_optimizations(value=True)
        layout.setSpacing(min(self.thumb_size // 10, 12))
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # TODO - init after library is loaded, it can have different page_size
        for _ in range(self.filter.page_size):
            item_thumb = ItemThumb(
                None,
                self.lib,
                self,
                (self.thumb_size, self.thumb_size),
                bool(
                    self.settings.value(SettingItems.SHOW_FILENAMES, defaultValue=True, type=bool)
                ),
            )

            layout.addWidget(item_thumb)
            self.item_thumbs.append(item_thumb)

        self.flow_container: QWidget = QWidget()
        self.flow_container.setObjectName("flowContainer")
        self.flow_container.setLayout(layout)
        sa: QScrollArea = self.main_window.scrollArea
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sa.setWidgetResizable(True)
        sa.setWidget(self.flow_container)

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

        self.set_macro_menu_viability()
        self.preview_panel.update_widgets()

    def set_macro_menu_viability(self):
        self.autofill_action.setDisabled(not self.selected)

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
            self.main_window.searchFieldCompletionList.setStringList(completion_list)

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
            completion_list = list(map(lambda x: prefix + "path:" + x, self.lib.get_paths()))
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
            completion_list != self.main_window.searchFieldCompletionList.stringList()
            or self.main_window.searchFieldCompletionList == []
        )
        if update_completion_list:
            self.main_window.searchFieldCompletionList.setStringList(completion_list)

    def update_thumbs(self):
        """Update search thumbnails."""
        # start_time = time.time()
        # logger.info(f'Current Page: {self.cur_page_idx}, Stack Length:{len(self.nav_stack)}')
        with self.thumb_job_queue.mutex:
            # Cancels all thumb jobs waiting to be started
            self.thumb_job_queue.queue.clear()
            self.thumb_job_queue.all_tasks_done.notify_all()
            self.thumb_job_queue.not_full.notify_all()
            # Stops in-progress jobs from finishing
            ItemThumb.update_cutoff = time.time()

        ratio: float = self.main_window.devicePixelRatio()
        base_size: tuple[int, int] = (self.thumb_size, self.thumb_size)

        # scrollbar: QScrollArea = self.main_window.scrollArea
        # scrollbar.verticalScrollBar().setValue(scrollbar_pos)
        self.flow_container.layout().update()
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

        for it in self.item_thumbs:
            if it.item_id in item_ids:
                for badge_type, value in badge_values.items():
                    if add_tags:
                        it.toggle_item_tag(it.item_id, value, BADGE_TAGS[badge_type])
                    it.assign_badge(badge_type, value)

    def filter_items(self, filter: FilterState | None = None) -> None:
        if not self.lib.library_dir:
            logger.info("Library not loaded")
            return
        assert self.lib.engine

        if filter:
            self.filter = dataclasses.replace(self.filter, **dataclasses.asdict(filter))
        else:
            self.filter.sorting_mode = self.sorting_mode
            self.filter.ascending = self.sorting_direction

        # inform user about running search
        self.main_window.statusbar.showMessage(Translations["status.library_search_query"])
        self.main_window.statusbar.repaint()

        # search the library
        start_time = time.time()
        results = self.lib.search_library(self.filter)
        logger.info("items to render", count=len(results))
        end_time = time.time()

        # inform user about completed search
        self.main_window.statusbar.showMessage(
            Translations.translate_formatted(
                "status.results_found",
                count=results.total_count,
                time_span=format_timespan(end_time - start_time),
            )
        )

        # update page content
        self.frame_content = [item.id for item in results.items]
        self.update_thumbs()

        # update pagination
        self.pages_count = math.ceil(results.total_count / self.filter.page_size)
        self.main_window.pagination.update_buttons(
            self.pages_count, self.filter.page_index, emit=False
        )

    def remove_recent_library(self, item_key: str):
        self.settings.beginGroup(SettingItems.LIBS_LIST)
        self.settings.remove(item_key)
        self.settings.endGroup()
        self.settings.sync()

    def update_libs_list(self, path: Path | str):
        """Add library to list in SettingItems.LIBS_LIST."""
        item_limit: int = 5
        path = Path(path)

        self.settings.beginGroup(SettingItems.LIBS_LIST)

        all_libs = {str(time.time()): str(path)}

        for item_key in self.settings.allKeys():
            item_path = str(self.settings.value(item_key, type=str))
            if Path(item_path) != path:
                all_libs[item_key] = item_path

        # sort items, most recent first
        all_libs_list = sorted(all_libs.items(), key=lambda item: item[0], reverse=True)

        # remove previously saved items
        self.settings.remove("")

        for item_key, item_value in all_libs_list[:item_limit]:
            self.settings.setValue(item_key, item_value)

        self.settings.endGroup()
        self.settings.sync()
        self.update_recent_lib_menu()

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
            action.triggered.connect(lambda checked=False, p=path: self.open_library(p))
            actions.append(action)

        clear_recent_action = QAction(self.open_recent_library_menu)
        Translations.translate_qobject(clear_recent_action, "menu.file.clear_recent_libraries")
        clear_recent_action.triggered.connect(self.clear_recent_libs)
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

    def clear_recent_libs(self):
        """Clear the list of recent libraries from the settings file."""
        settings = self.settings
        settings.beginGroup(SettingItems.LIBS_LIST)
        self.settings.remove("")
        self.settings.endGroup()
        self.settings.sync()
        self.update_recent_lib_menu()

    def open_library(self, path: Path) -> None:
        """Open a TagStudio library."""
        translation_params = {"key": "splash.opening_library", "library_path": str(path)}
        Translations.translate_with_setter(
            self.main_window.landing_widget.set_status_label, **translation_params
        )
        self.main_window.statusbar.showMessage(
            Translations.translate_formatted(**translation_params), 3
        )
        self.main_window.repaint()

        if self.lib.library_dir:
            self.close_library()

        open_status: LibraryStatus = None
        try:
            open_status = self.lib.open_library(path)
        except Exception as e:
            logger.exception(e)
            open_status = LibraryStatus(success=False, library_path=path, message=type(e).__name__)

        # Migration is required
        if open_status.json_migration_req:
            self.migration_modal = JsonMigrationModal(path)
            self.migration_modal.migration_finished.connect(
                lambda: self.init_library(path, self.lib.open_library(path))
            )
            self.main_window.landing_widget.set_status_label("")
            self.migration_modal.paged_panel.show()
        else:
            self.init_library(path, open_status)

    def init_library(self, path: Path, open_status: LibraryStatus):
        if not open_status.success:
            self.show_error_message(
                open_status.message or Translations["window.message.error_opening_library"]
            )
            return open_status

        self.init_workers()

        self.filter.page_size = self.lib.prefs(LibraryPrefs.PAGE_SIZE)

        # TODO - make this call optional
        if self.lib.entries_count < 10000:
            self.add_new_files_callback()

        self.update_libs_list(path)
        Translations.translate_with_setter(
            self.main_window.setWindowTitle,
            "app.title",
            base_title=self.base_title,
            library_dir=self.lib.library_dir,
        )
        self.main_window.setAcceptDrops(True)

        self.selected.clear()
        self.preview_panel.update_widgets()

        # page (re)rendering, extract eventually
        self.filter_items()

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
