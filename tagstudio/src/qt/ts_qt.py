# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

# SIGTERM handling based on the implementation by Virgil Dupras for dupeGuru:
# https://github.com/arsenetar/dupeguru/blob/master/run.py#L71

"""A Qt driver for TagStudio."""

import ctypes
import dataclasses
import math
import os
import sys
import time
import webbrowser
from collections.abc import Sequence
from itertools import zip_longest
from pathlib import Path
from queue import Queue

# this import has side-effect of import PySide resources
import src.qt.resources_rc  # noqa: F401
import structlog
from humanfriendly import format_timespan
from PySide6 import QtCore
from PySide6.QtCore import (
    QObject,
    QSettings,
    Qt,
    QThread,
    QThreadPool,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QAction,
    QColor,
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
from src.core.library.alchemy.enums import (
    FieldTypeEnum,
    FilterState,
    ItemType,
    SearchMode,
)
from src.core.library.alchemy.fields import _FieldID
from src.core.library.alchemy.library import LibraryStatus
from src.core.ts_core import TagStudioCore
from src.core.utils.refresh_dir import RefreshDirTracker
from src.core.utils.web import strip_web_protocol
from src.qt.flowlayout import FlowLayout
from src.qt.helpers.custom_runnable import CustomRunnable
from src.qt.helpers.function_iterator import FunctionIterator
from src.qt.main_window import Ui_MainWindow
from src.qt.modals.build_tag import BuildTagPanel
from src.qt.modals.file_extension import FileExtensionModal
from src.qt.modals.fix_dupes import FixDupeFilesModal
from src.qt.modals.fix_unlinked import FixUnlinkedEntriesModal
from src.qt.modals.folders_to_tags import FoldersToTagsModal
from src.qt.modals.tag_database import TagDatabasePanel
from src.qt.resource_manager import ResourceManager
from src.qt.widgets.item_thumb import BadgeType, ItemThumb
from src.qt.widgets.panel import PanelModal
from src.qt.widgets.preview_panel import PreviewPanel
from src.qt.widgets.progress import ProgressWidget
from src.qt.widgets.thumb_renderer import ThumbRenderer

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

    def __init__(self, backend, args):
        super().__init__()
        # prevent recursive badges update when multiple items selected
        self.badge_update_lock = False
        self.lib = backend.Library()
        self.rm: ResourceManager = ResourceManager()
        self.args = args
        self.frame_content = []
        self.filter = FilterState()
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

        # grid indexes of selected items
        self.selected: list[int] = []

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
            None,
            "Open/Create Library",
            "/",
            QFileDialog.Option.ShowDirsOnly,
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
        self.main_window.mousePressEvent = self.mouse_navigation  # type: ignore
        # self.main_window.setStyleSheet(
        # 	f'QScrollBar::{{background:red;}}'
        # 	)

        # # self.main_window.windowFlags() &
        # # self.main_window.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        # self.main_window.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)
        # self.main_window.setWindowFlag(Qt.WindowType.WindowTransparentForInput, False)
        # self.main_window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # self.windowFX = WindowEffect()
        # self.windowFX.setAcrylicEffect(self.main_window.winId())

        splash_pixmap = QPixmap(":/images/splash.png")
        splash_pixmap.setDevicePixelRatio(self.main_window.devicePixelRatio())
        self.splash = QSplashScreen(splash_pixmap, Qt.WindowType.WindowStaysOnTopHint)
        # self.splash.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.splash.show()

        if os.name == "nt":
            appid = "cyanvoxel.tagstudio.9"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)  # type: ignore

        if sys.platform != "darwin":
            icon = QIcon()
            icon.addFile(str(icon_path))
            app.setWindowIcon(icon)

        menu_bar = QMenuBar(self.main_window)
        self.main_window.setMenuBar(menu_bar)
        menu_bar.setNativeMenuBar(True)

        file_menu = QMenu("&File", menu_bar)
        edit_menu = QMenu("&Edit", menu_bar)
        tools_menu = QMenu("&Tools", menu_bar)
        macros_menu = QMenu("&Macros", menu_bar)
        window_menu = QMenu("&Window", menu_bar)
        help_menu = QMenu("&Help", menu_bar)

        # File Menu ============================================================
        # file_menu.addAction(QAction('&New Library', menu_bar))
        # file_menu.addAction(QAction('&Open Library', menu_bar))

        open_library_action = QAction("&Open/Create Library", menu_bar)
        open_library_action.triggered.connect(lambda: self.open_library_from_dialog())
        open_library_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_O,
            )
        )
        open_library_action.setToolTip("Ctrl+O")
        file_menu.addAction(open_library_action)

        save_library_backup_action = QAction("&Save Library Backup", menu_bar)
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

        # refresh_lib_action = QAction('&Refresh Directories', self.main_window)
        # refresh_lib_action.triggered.connect(lambda: self.lib.refresh_dir())
        add_new_files_action = QAction("&Refresh Directories", menu_bar)
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
        # file_menu.addAction(refresh_lib_action)
        file_menu.addAction(add_new_files_action)
        file_menu.addSeparator()

        close_library_action = QAction("&Close Library", menu_bar)
        close_library_action.triggered.connect(self.close_library)
        file_menu.addAction(close_library_action)

        # Edit Menu ============================================================
        new_tag_action = QAction("New &Tag", menu_bar)
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

        select_all_action = QAction("Select All", menu_bar)
        select_all_action.triggered.connect(self.select_all_action_callback)
        select_all_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_A,
            )
        )
        select_all_action.setToolTip("Ctrl+A")
        edit_menu.addAction(select_all_action)

        clear_select_action = QAction("Clear Selection", menu_bar)
        clear_select_action.triggered.connect(self.clear_select_action_callback)
        clear_select_action.setShortcut(QtCore.Qt.Key.Key_Escape)
        clear_select_action.setToolTip("Esc")
        edit_menu.addAction(clear_select_action)

        edit_menu.addSeparator()

        manage_file_extensions_action = QAction("Manage File Extensions", menu_bar)
        manage_file_extensions_action.triggered.connect(self.show_file_extension_modal)
        edit_menu.addAction(manage_file_extensions_action)

        tag_database_action = QAction("Manage Tags", menu_bar)
        tag_database_action.triggered.connect(lambda: self.show_tag_database())
        edit_menu.addAction(tag_database_action)

        check_action = QAction("Open library on start", self)
        check_action.setCheckable(True)
        check_action.setChecked(
            bool(self.settings.value(SettingItems.START_LOAD_LAST, defaultValue=True, type=bool))
        )
        check_action.triggered.connect(
            lambda checked: self.settings.setValue(SettingItems.START_LOAD_LAST, checked)
        )
        window_menu.addAction(check_action)

        # Tools Menu ===========================================================
        def create_fix_unlinked_entries_modal():
            if not hasattr(self, "unlinked_modal"):
                self.unlinked_modal = FixUnlinkedEntriesModal(self.lib, self)
            self.unlinked_modal.show()

        fix_unlinked_entries_action = QAction("Fix &Unlinked Entries", menu_bar)
        fix_unlinked_entries_action.triggered.connect(create_fix_unlinked_entries_modal)
        tools_menu.addAction(fix_unlinked_entries_action)

        def create_dupe_files_modal():
            if not hasattr(self, "dupe_modal"):
                self.dupe_modal = FixDupeFilesModal(self.lib, self)
            self.dupe_modal.show()

        fix_dupe_files_action = QAction("Fix Duplicate &Files", menu_bar)
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
                self.preview_panel.update_widgets(),
            )
        )
        macros_menu.addAction(self.autofill_action)

        show_libs_list_action = QAction("Show Recent Libraries", menu_bar)
        show_libs_list_action.setCheckable(True)
        show_libs_list_action.setChecked(
            bool(self.settings.value(SettingItems.WINDOW_SHOW_LIBS, defaultValue=True, type=bool))
        )
        show_libs_list_action.triggered.connect(
            lambda checked: (
                self.settings.setValue(SettingItems.WINDOW_SHOW_LIBS, checked),
                self.toggle_libs_list(checked),
            )
        )
        window_menu.addAction(show_libs_list_action)

        def create_folders_tags_modal():
            if not hasattr(self, "folders_modal"):
                self.folders_modal = FoldersToTagsModal(self.lib, self)
            self.folders_modal.show()

        folders_to_tags_action = QAction("Folders to Tags", menu_bar)
        folders_to_tags_action.triggered.connect(create_folders_tags_modal)
        macros_menu.addAction(folders_to_tags_action)

        # Help Menu ==========================================================
        self.repo_action = QAction("Visit GitHub Repository", menu_bar)
        self.repo_action.triggered.connect(
            lambda: webbrowser.open("https://github.com/TagStudioDev/TagStudio")
        )
        help_menu.addAction(self.repo_action)
        self.set_macro_menu_viability()

        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(edit_menu)
        menu_bar.addMenu(tools_menu)
        menu_bar.addMenu(macros_menu)
        menu_bar.addMenu(window_menu)
        menu_bar.addMenu(help_menu)

        self.preview_panel = PreviewPanel(self.lib, self)
        splitter = self.main_window.splitter
        splitter.addWidget(self.preview_panel)

        QFontDatabase.addApplicationFont(
            str(Path(__file__).parents[2] / "resources/qt/fonts/Oxanium-Bold.ttf")
        )

        self.thumb_sizes: list[tuple[str, int]] = [
            ("Extra Large Thumbnails", 256),
            ("Large Thumbnails", 192),
            ("Medium Thumbnails", 128),
            ("Small Thumbnails", 96),
            ("Mini Thumbnails", 76),
        ]
        self.item_thumbs: list[ItemThumb] = []
        self.thumb_renderers: list[ThumbRenderer] = []
        self.filter = FilterState()
        self.init_library_window()

        path_result = self.evaluate_path(self.args.open)
        # check status of library path evaluating
        if path_result.success and path_result.library_path:
            self.splash.showMessage(
                f'Opening Library "{path_result.library_path}"...',
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
        msg_box.setWindowTitle("Error")
        msg_box.addButton("Close", QMessageBox.ButtonRole.AcceptRole)

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
            lambda: self.filter_items(FilterState(query=self.main_window.searchField.text()))
        )
        # Search Field
        search_field: QLineEdit = self.main_window.searchField
        search_field.returnPressed.connect(
            # TODO - parse search field for filters
            lambda: self.filter_items(FilterState(query=self.main_window.searchField.text()))
        )
        # Search Type Selector
        search_type_selector: QComboBox = self.main_window.comboBox_2
        search_type_selector.currentIndexChanged.connect(
            lambda: self.set_search_type(SearchMode(search_type_selector.currentIndex()))
        )
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
        self.preview_panel.update_widgets()

    def toggle_libs_list(self, value: bool):
        if value:
            self.preview_panel.libs_flow_container.show()
        else:
            self.preview_panel.libs_flow_container.hide()
        self.preview_panel.update()

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
        self.main_window.statusbar.showMessage("Closing Library...")
        start_time = time.time()

        self.settings.setValue(SettingItems.LAST_LIBRARY, str(self.lib.library_dir))
        self.settings.sync()

        self.lib.close()

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
            f"Library Closed ({format_timespan(end_time - start_time)})"
        )

    def backup_library(self):
        logger.info("Backing Up Library...")
        self.main_window.statusbar.showMessage("Saving Library...")
        start_time = time.time()
        target_path = self.lib.save_library_backup_to_disk()
        end_time = time.time()
        self.main_window.statusbar.showMessage(
            f'Library Backup Saved at: "{target_path}" ({format_timespan(end_time - start_time)})'
        )

    def add_tag_action_callback(self):
        self.modal = PanelModal(
            BuildTagPanel(self.lib),
            "New Tag",
            "Add Tag",
            has_save=True,
        )

        panel: BuildTagPanel = self.modal.widget
        self.modal.saved.connect(
            lambda: (
                self.lib.add_tag(panel.build_tag(), panel.subtags),
                self.modal.hide(),
            )
        )
        self.modal.show()

    def select_all_action_callback(self):
        self.selected = list(range(0, len(self.frame_content)))

        for grid_idx in self.selected:
            self.item_thumbs[grid_idx].thumb_button.set_selected(True)

        self.set_macro_menu_viability()
        self.preview_panel.update_widgets()

    def clear_select_action_callback(self):
        self.selected.clear()
        for item in self.item_thumbs:
            item.thumb_button.set_selected(False)

        self.set_macro_menu_viability()
        self.preview_panel.update_widgets()

    def show_tag_database(self):
        self.modal = PanelModal(
            TagDatabasePanel(self.lib), "Library Tags", "Library Tags", has_save=False
        )
        self.modal.show()

    def show_file_extension_modal(self):
        panel = FileExtensionModal(self.lib)
        self.modal = PanelModal(
            panel,
            "File Extensions",
            "File Extensions",
            has_save=True,
        )

        self.modal.saved.connect(lambda: (panel.save(), self.filter_items()))
        self.modal.show()

    def add_new_files_callback(self):
        """Run when user initiates adding new files to the Library."""
        tracker = RefreshDirTracker(self.lib)

        pw = ProgressWidget(
            window_title="Refreshing Directories",
            label_text="Scanning Directories for New Files...\nPreparing...",
            cancel_button_text=None,
            minimum=0,
            maximum=0,
        )
        pw.show()

        iterator = FunctionIterator(lambda: tracker.refresh_dir(self.lib.library_dir))
        iterator.value.connect(
            lambda x: (
                pw.update_progress(x + 1),
                pw.update_label(
                    f"Scanning Directories for New Files...\n{x + 1}"
                    f" File{"s" if x + 1 != 1 else ""} Searched,"
                    f" {tracker.files_count} New Files Found"
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
        # pb = QProgressDialog(
        #     f"Running Configured Macros on 1/{len(new_ids)} New Entries", None, 0, len(new_ids)
        # )
        # pb.setFixedSize(432, 112)
        # pb.setWindowFlags(pb.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        # pb.setWindowTitle('Running Macros')
        # pb.setWindowModality(Qt.WindowModality.ApplicationModal)
        # pb.show()

        # r = CustomRunnable(lambda: self.new_file_macros_runnable(pb, new_ids))
        # r.done.connect(lambda: (pb.hide(), pb.deleteLater(), self.filter_items('')))
        # r.run()
        # # QThreadPool.globalInstance().start(r)

        # # self.main_window.statusbar.showMessage(
        # #     f"Running configured Macros on {len(new_ids)} new Entries...", 3
        # # )

        # # pb.hide()

        files_count = tracker.files_count

        iterator = FunctionIterator(tracker.save_new_files)
        pw = ProgressWidget(
            window_title="Running Macros on New Entries",
            label_text=f"Running Configured Macros on 1/{files_count} New Entries",
            cancel_button_text=None,
            minimum=0,
            maximum=files_count,
        )
        pw.show()
        iterator.value.connect(
            lambda x: (
                pw.update_progress(x + 1),
                pw.update_label(f"Running Configured Macros on {x + 1}/{files_count} New Entries"),
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
        # sleep(1)
        # for i, id in enumerate(new_ids):
        # 	# pb.setValue(i)
        # 	# pb.setLabelText(f'Running Configured Macros on {i}/{len(new_ids)} New Entries')
        # 	# self.run_macro('autofill', id)

        # NOTE: I don't know. I don't know why it needs this. The whole program
        # falls apart if this method doesn't run, and it DOESN'T DO ANYTHING
        yield 0

        # self.main_window.statusbar.showMessage('', 3)

        # sleep(5)
        # pb.deleteLater()

    def run_macros(self, name: MacroID, grid_idx: list[int]):
        """Run a specific Macro on a group of given entry_ids."""
        for gid in grid_idx:
            self.run_macro(name, gid)

    def run_macro(self, name: MacroID, grid_idx: int):
        """Run a specific Macro on an Entry given a Macro name."""
        entry = self.frame_content[grid_idx]
        ful_path = self.lib.library_dir / entry.path
        source = entry.path.parts[0]

        logger.info(
            "running macro",
            source=source,
            macro=name,
            entry_id=entry.id,
            grid_idx=grid_idx,
        )

        if name == MacroID.AUTOFILL:
            for macro_id in MacroID:
                if macro_id == MacroID.AUTOFILL:
                    continue
                self.run_macro(macro_id, entry.id)

        elif name == MacroID.SIDECAR:
            parsed_items = TagStudioCore.get_gdl_sidecar(ful_path, source)
            for field_id, value in parsed_items.items():
                self.lib.add_entry_field_type(
                    entry.id,
                    field_id=field_id,
                    value=value,
                )

        elif name == MacroID.BUILD_URL:
            url = TagStudioCore.build_url(entry.id, source)
            self.lib.add_entry_field_type(entry.id, field_id=_FieldID.SOURCE, value=url)
        elif name == MacroID.MATCH:
            TagStudioCore.match_conditions(self.lib, entry.id)
        elif name == MacroID.CLEAN_URL:
            for field in entry.text_fields:
                if field.type.type == FieldTypeEnum.TEXT_LINE and field.value:
                    self.lib.update_entry_field(
                        entry_ids=entry.id,
                        content=strip_web_protocol(field.value),
                    )

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
            it.setMinimumSize(self.thumb_size, self.thumb_size)
            it.setMaximumSize(self.thumb_size, self.thumb_size)
            it.thumb_button.thumb_size = (self.thumb_size, self.thumb_size)
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
        for grid_idx in range(self.filter.page_size):
            item_thumb = ItemThumb(
                None, self.lib, self, (self.thumb_size, self.thumb_size), grid_idx
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

    def select_item(self, grid_index: int, append: bool, bridge: bool):
        """Select one or more items in the Thumbnail Grid."""
        logger.info("selecting item", grid_index=grid_index, append=append, bridge=bridge)
        if append:
            if grid_index not in self.selected:
                self.selected.append(grid_index)
                self.item_thumbs[grid_index].thumb_button.set_selected(True)
            else:
                self.selected.remove(grid_index)
                self.item_thumbs[grid_index].thumb_button.set_selected(False)

        elif bridge and self.selected:
            select_from = min(self.selected)
            select_to = max(self.selected)

            if select_to < grid_index:
                index_range = range(select_from, grid_index + 1)
            else:
                index_range = range(grid_index, select_to + 1)

            self.selected = list(index_range)

            for selected_idx in self.selected:
                self.item_thumbs[selected_idx].thumb_button.set_selected(True)
        else:
            self.selected = [grid_index]
            for thumb_idx, item_thumb in enumerate(self.item_thumbs):
                item_matched = thumb_idx == grid_index
                item_thumb.thumb_button.set_selected(item_matched)

        # NOTE: By using the preview panel's "set_tags_updated_slot" method,
        # only the last of multiple identical item selections are connected.
        # If attaching the slot to multiple duplicate selections is needed,
        # just bypass the method and manually disconnect and connect the slots.
        if len(self.selected) == 1:
            for it in self.item_thumbs:
                if it.item_id == id:
                    self.preview_panel.set_tags_updated_slot(it.refresh_badge)

        self.set_macro_menu_viability()
        self.preview_panel.update_widgets()

    def set_macro_menu_viability(self):
        self.autofill_action.setDisabled(not self.selected)

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

        for idx, (entry, item_thumb) in enumerate(
            zip_longest(self.frame_content, self.item_thumbs)
        ):
            if not entry:
                item_thumb.hide()
                continue

            filepath = self.lib.library_dir / entry.path
            item_thumb = self.item_thumbs[idx]
            item_thumb.set_mode(ItemType.ENTRY)
            item_thumb.set_item_id(entry)

            # TODO - show after item is rendered
            item_thumb.show()

            self.thumb_job_queue.put(
                (
                    item_thumb.renderer.render,
                    (sys.float_info.max, "", base_size, ratio, True, True),
                )
            )

            entry_tag_ids = {tag.id for tag in entry.tags}
            item_thumb.assign_badge(BadgeType.ARCHIVED, TAG_ARCHIVED in entry_tag_ids)
            item_thumb.assign_badge(BadgeType.FAVORITE, TAG_FAVORITE in entry_tag_ids)
            item_thumb.update_clickable(
                clickable=(
                    lambda checked=False, index=idx: self.select_item(
                        index,
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
            is_selected = (item_thumb.mode, item_thumb.item_id) in self.selected
            item_thumb.thumb_button.set_selected(is_selected)

            self.thumb_job_queue.put(
                (
                    item_thumb.renderer.render,
                    (time.time(), filepath, base_size, ratio, False, True),
                )
            )

    def update_badges(self, grid_item_ids: Sequence[int] = None):
        if not grid_item_ids:
            # no items passed, update all items in grid
            grid_item_ids = range(min(len(self.item_thumbs), len(self.frame_content)))

        logger.info("updating badges for items", grid_item_ids=grid_item_ids)

        for grid_idx in grid_item_ids:
            # get the entry from grid to avoid loading from db again
            entry = self.frame_content[grid_idx]
            self.item_thumbs[grid_idx].refresh_badge(entry)

    def filter_items(self, filter: FilterState | None = None) -> None:
        assert self.lib.engine

        if filter:
            self.filter = dataclasses.replace(self.filter, **dataclasses.asdict(filter))

        self.main_window.statusbar.showMessage(f'Searching Library: "{self.filter.summary}"')
        self.main_window.statusbar.repaint()
        start_time = time.time()

        results = self.lib.search_library(self.filter)

        logger.info("items to render", count=len(results))

        end_time = time.time()
        if self.filter.summary:
            # fmt: off
            self.main_window.statusbar.showMessage(
                f"{results.total_count} Results Found for \"{self.filter.summary}\""
                f" ({format_timespan(end_time - start_time)})"
            )
            # fmt: on
        else:
            self.main_window.statusbar.showMessage(
                f"{results.total_count} Results ({format_timespan(end_time - start_time)})"
            )

        # update page content
        self.frame_content = results.items
        self.update_thumbs()

        # update pagination
        self.pages_count = math.ceil(results.total_count / self.filter.page_size)
        self.main_window.pagination.update_buttons(
            self.pages_count, self.filter.page_index, emit=False
        )

    def set_search_type(self, mode: SearchMode = SearchMode.AND):
        self.filter_items(
            FilterState(
                search_mode=mode,
                path=self.main_window.searchField.text(),
            )
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
        self.settings.clear()

        for item_key, item_value in all_libs_list[:item_limit]:
            self.settings.setValue(item_key, item_value)

        self.settings.endGroup()
        self.settings.sync()

    def open_library(self, path: Path) -> LibraryStatus:
        """Open a TagStudio library."""
        open_message: str = f'Opening Library "{str(path)}"...'
        self.main_window.landing_widget.set_status_label(open_message)
        self.main_window.statusbar.showMessage(open_message, 3)
        self.main_window.repaint()

        open_status = self.lib.open_library(path)
        if not open_status.success:
            self.show_error_message(open_status.message or "Error opening library.")
            return open_status

        self.init_workers()

        self.filter.page_size = self.lib.prefs(LibraryPrefs.PAGE_SIZE)

        # TODO - make this call optional
        self.add_new_files_callback()

        self.update_libs_list(path)
        title_text = f"{self.base_title} - Library '{self.lib.library_dir}'"
        self.main_window.setWindowTitle(title_text)

        self.selected.clear()
        self.preview_panel.update_widgets()

        # page (re)rendering, extract eventually
        self.filter_items()

        self.main_window.toggle_landing_page(enabled=False)
        return open_status
