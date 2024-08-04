# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

# SIGTERM handling based on the implementation by Virgil Dupras for dupeGuru:
# https://github.com/arsenetar/dupeguru/blob/master/run.py#L71

"""A Qt driver for TagStudio."""

import ctypes
import math
import os
import sys
import time
import typing
import webbrowser
from itertools import zip_longest
from pathlib import Path
from queue import Queue

import structlog
from PySide6 import QtCore
from PySide6.QtCore import (
    QObject,
    QThread,
    Signal,
    Qt,
    QThreadPool,
    QTimer,
    QSettings,
)
from PySide6.QtGui import (
    QGuiApplication,
    QPixmap,
    QMouseEvent,
    QColor,
    QAction,
    QFontDatabase,
    QIcon,
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QScrollArea,
    QFileDialog,
    QSplashScreen,
    QMenu,
    QMenuBar,
    QComboBox,
)
from humanfriendly import format_timespan

from src.core.enums import SettingItems

from src.core.constants import (
    BACKUP_FOLDER_NAME,
    TS_FOLDER_NAME,
    VERSION_BRANCH,
    VERSION,
)
from src.core.library.alchemy.enums import SearchMode, FilterState, ItemType
from src.core.utils.web import strip_web_protocol
from src.qt.flowlayout import FlowLayout  # type: ignore
from src.qt.main_window import Ui_MainWindow
from src.qt.helpers.function_iterator import FunctionIterator
from src.qt.helpers.custom_runnable import CustomRunnable
from src.qt.resource_manager import ResourceManager
from src.qt.widgets.panel import PanelModal
from src.qt.widgets.thumb_renderer import ThumbRenderer
from src.qt.widgets.progress import ProgressWidget
from src.qt.widgets.preview_panel import PreviewPanel
from src.qt.widgets.item_thumb import ItemThumb
from src.qt.modals.build_tag import BuildTagPanel
from src.qt.modals.tag_database import TagDatabasePanel
from src.qt.modals.file_extension import FileExtensionModal
from src.qt.modals.fix_unlinked import FixUnlinkedEntriesModal
from src.qt.modals.fix_dupes import FixDupeFilesModal
from src.qt.modals.folders_to_tags import FoldersToTagsModal

# this import has side-effect of import PySide resources
import src.qt.resources_rc  # pylint: disable=unused-import

# SIGQUIT is not defined on Windows
if sys.platform == "win32":
    from signal import signal, SIGINT, SIGTERM

    SIGQUIT = SIGTERM
else:
    from signal import signal, SIGINT, SIGTERM, SIGQUIT

ERROR = f"[ERROR]"
WARNING = f"[WARNING]"
INFO = f"[INFO]"

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


class QtDriver(QObject):
    """A Qt GUI frontend driver for TagStudio."""

    SIGTERM = Signal()

    preview_panel: PreviewPanel

    def __init__(self, backend, args):
        super().__init__()
        # self.core: TagStudioCore = core
        self.lib = backend.Library()
        self.rm: ResourceManager = ResourceManager()
        self.args = args
        self.frame_content = []
        self.filter = FilterState()

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

        # indexes of selected items
        self.selected: list[int] = []

        self.SIGTERM.connect(self.handleSIGTERM)

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

        max_threads = os.cpu_count()
        if args.ci:
            # spawn only single worker in CI environment
            max_threads = 1

        for i in range(max_threads):
            # TODO - uncomment
            # thread = threading.Thread(target=self.consumer, name=f'ThumbRenderer_{i}',args=(), daemon=True)
            # thread.start()
            thread = Consumer(self.thumb_job_queue)
            thread.setObjectName(f"ThumbRenderer_{i}")
            self.thumb_threads.append(thread)
            thread.start()

    def open_library_from_dialog(self):
        dir = QFileDialog.getExistingDirectory(
            None,
            "Open/Create Library",
            "/",
            QFileDialog.ShowDirsOnly,  # type: ignore
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
        home_path = Path(__file__).parent / "ui/home.ui"
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
        self.splash = QSplashScreen(splash_pixmap, Qt.WindowStaysOnTopHint)  # type: ignore
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

        save_library_action = QAction("&Save Library", menu_bar)
        save_library_action.triggered.connect(
            lambda: self.callback_library_needed_check(self.save_library)
        )
        save_library_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.ControlModifier),
                QtCore.Qt.Key.Key_S,
            )
        )
        save_library_action.setStatusTip("Ctrl+S")
        file_menu.addAction(save_library_action)

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
        close_library_action.triggered.connect(lambda: self.close_library())
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
        manage_file_extensions_action.triggered.connect(
            lambda: self.show_file_extension_modal()
        )
        edit_menu.addAction(manage_file_extensions_action)

        tag_database_action = QAction("Manage Tags", menu_bar)
        tag_database_action.triggered.connect(lambda: self.show_tag_database())
        edit_menu.addAction(tag_database_action)

        check_action = QAction("Open library on start", self)
        check_action.setCheckable(True)
        check_action.setChecked(
            self.settings.value(SettingItems.START_LOAD_LAST, True, type=bool)  # type: ignore[arg-type]
        )
        check_action.triggered.connect(
            lambda checked: self.settings.setValue(
                SettingItems.START_LOAD_LAST, checked
            )
        )
        window_menu.addAction(check_action)

        # Tools Menu ===========================================================
        fix_unlinked_entries_action = QAction("Fix &Unlinked Entries", menu_bar)
        fue_modal = FixUnlinkedEntriesModal(self.lib, self)
        fix_unlinked_entries_action.triggered.connect(lambda: fue_modal.show())
        tools_menu.addAction(fix_unlinked_entries_action)

        fix_dupe_files_action = QAction("Fix Duplicate &Files", menu_bar)
        fdf_modal = FixDupeFilesModal(self.lib, self)
        fix_dupe_files_action.triggered.connect(lambda: fdf_modal.show())
        tools_menu.addAction(fix_dupe_files_action)

        # create_collage_action = QAction("Create Collage", menu_bar)
        # create_collage_action.triggered.connect(lambda: self.create_collage())
        # tools_menu.addAction(create_collage_action)

        # Macros Menu ==========================================================
        self.autofill_action = QAction("Autofill", menu_bar)
        self.autofill_action.triggered.connect(
            lambda: (
                self.run_macros("autofill", self.selected),
                self.preview_panel.update_widgets(),
            )
        )
        macros_menu.addAction(self.autofill_action)

        self.sort_fields_action = QAction("&Sort Fields", menu_bar)
        self.sort_fields_action.triggered.connect(
            lambda: (
                self.run_macros(
                    "sort-fields",
                    self.selected,
                ),
                self.preview_panel.update_widgets(),
            )
        )
        self.sort_fields_action.setShortcut(
            QtCore.QKeyCombination(
                QtCore.Qt.KeyboardModifier(QtCore.Qt.KeyboardModifier.AltModifier),
                QtCore.Qt.Key.Key_S,
            )
        )
        self.sort_fields_action.setToolTip("Alt+S")
        macros_menu.addAction(self.sort_fields_action)

        show_libs_list_action = QAction("Show Recent Libraries", menu_bar)
        show_libs_list_action.setCheckable(True)
        show_libs_list_action.setChecked(
            self.settings.value(SettingItems.WINDOW_SHOW_LIBS, True, type=bool)  # type: ignore
        )
        show_libs_list_action.triggered.connect(
            lambda checked: (
                self.settings.setValue(SettingItems.WINDOW_SHOW_LIBS, checked),  # type: ignore
                self.toggle_libs_list(checked),
            )
        )
        window_menu.addAction(show_libs_list_action)

        folders_to_tags_action = QAction("Folders to Tags", menu_bar)
        ftt_modal = FoldersToTagsModal(self.lib, self)
        folders_to_tags_action.triggered.connect(lambda: ftt_modal.show())
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
        l: QHBoxLayout = self.main_window.splitter
        l.addWidget(self.preview_panel)

        QFontDatabase.addApplicationFont(
            str(Path(__file__).parents[2] / "resources/qt/fonts/Oxanium-Bold.ttf")
        )

        self.thumb_size = 128
        self.item_thumbs: list[ItemThumb] = []
        self.thumb_renderers: list[ThumbRenderer] = []

        self.init_library_window()

        lib = None
        if self.args.open:
            lib = self.args.open
        elif self.settings.value(SettingItems.START_LOAD_LAST, True, type=bool):
            lib = self.settings.value(SettingItems.LAST_LIBRARY)

            # TODO: Remove this check if the library is no longer saved with files
            if lib and not (Path(lib) / TS_FOLDER_NAME).exists():
                logger.error(
                    f"[QT DRIVER] {TS_FOLDER_NAME} folder in {lib} does not exist."
                )
                self.settings.setValue(SettingItems.LAST_LIBRARY, "")
                lib = None

        if lib:
            self.splash.showMessage(
                f'Opening Library "{lib}"...',
                int(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter),
                QColor("#9782ff"),
            )
            self.open_library(lib)
            self.filter_items()

        if self.args.ci:
            # gracefully terminate the app in CI environment
            self.thumb_job_queue.put((self.SIGTERM.emit, []))

        app.exec()

        self.shutdown()

    def init_library_window(self):
        # self._init_landing_page() # Taken care of inside the widget now
        self._init_thumb_grid()

        # TODO: Put this into its own method that copies the font file(s) into memory
        # so the resource isn't being used, then store the specific size variations
        # in a global dict for methods to access for different DPIs.
        # adj_font_size = math.floor(12 * self.main_window.devicePixelRatio())
        # self.ext_font = ImageFont.truetype(os.path.normpath(f'{Path(__file__).parents[2]}/resources/qt/fonts/Oxanium-Bold.ttf'), adj_font_size)

        search_button: QPushButton = self.main_window.searchButton
        search_button.clicked.connect(
            lambda: self.filter_items(
                FilterState(name=self.main_window.searchField.text())
            )
        )
        search_field: QLineEdit = self.main_window.searchField
        search_field.returnPressed.connect(
            # search_field
            # TODO - parse search field for filters
            lambda: self.filter_items(
                FilterState(name=self.main_window.searchField.text())
            )
        )
        search_type_selector: QComboBox = self.main_window.comboBox_2
        search_type_selector.currentIndexChanged.connect(
            lambda: self.set_search_type(
                SearchMode(search_type_selector.currentIndex())
            )
        )

        back_button: QPushButton = self.main_window.backButton
        back_button.clicked.connect(lambda: self.page_move(-1))
        forward_button: QPushButton = self.main_window.forwardButton
        forward_button.clicked.connect(lambda: self.page_move(1))

        # NOTE: Putting this early will result in a white non-responsive
        # window until everything is loaded. Consider adding a splash screen
        # or implementing some clever loading tricks.
        self.main_window.show()
        self.main_window.activateWindow()
        self.main_window.toggle_landing_page(True)

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
        """Check if loaded library has valid path before executing the button function"""
        if self.lib.library_dir:
            func()

    def handleSIGTERM(self):
        self.shutdown()

    def shutdown(self):
        """Save Library on Application Exit"""
        if self.lib.library_dir:
            self.save_library()
            self.settings.setValue(SettingItems.LAST_LIBRARY, self.lib.library_dir)
            self.settings.sync()
        logger.info("[SHUTDOWN] Ending Thumbnail Threads...")
        for _ in self.thumb_threads:
            self.thumb_job_queue.put(Consumer.MARKER_QUIT)

        # wait for threads to quit
        for thread in self.thumb_threads:
            thread.quit()
            thread.wait()

        QApplication.quit()

    def update_filter(self, **kwargs):
        render = kwargs.pop("render", False)
        for key, value in kwargs.items():
            setattr(self.filter, key, value)

        if render:
            self.filter_items()

    def save_library(self, show_status=True):
        logger.info(f"Saving Library...")
        if show_status:
            self.main_window.statusbar.showMessage(f"Saving Library...")
            start_time = time.time()
        # This might still be able to error, if the selected directory deletes in a race condition
        # or something silly like that. Hence the loop, but if this is considered overkill, thats fair.
        while True:
            try:
                self.lib.save_library_to_disk()
                break
                # If the parent directory got moved, or deleted, prompt user for where to save.
            except FileNotFoundError:
                logger.info(
                    "Library parent directory not found, prompting user to select the directory"
                )
                dir = QFileDialog.getExistingDirectory(
                    None,
                    "Library Location not found, please select location to save Library",
                    "/",
                    QFileDialog.ShowDirsOnly,
                )
                if dir not in (None, ""):
                    self.lib.library_dir = dir
        if show_status:
            end_time = time.time()
            self.main_window.statusbar.showMessage(
                f"Library Saved! ({format_timespan(end_time - start_time)})"
            )

    def close_library(self):
        if not self.lib.library_dir:
            return

        logger.info(f"Closing Library...")
        self.main_window.statusbar.showMessage(f"Closing & Saving Library...")
        start_time = time.time()
        self.save_library(show_status=False)
        self.settings.setValue(SettingItems.LAST_LIBRARY, self.lib.library_dir)
        self.settings.sync()

        self.lib.clear_internal_vars()
        title_text = f"{self.base_title}"
        self.main_window.setWindowTitle(title_text)

        self.selected.clear()
        self.preview_panel.update_widgets()
        self.main_window.toggle_landing_page(True)

        end_time = time.time()
        self.main_window.statusbar.showMessage(
            f"Library Saved and Closed! ({format_timespan(end_time - start_time)})"
        )

    def backup_library(self):
        logger.info(f"Backing Up Library...")
        self.main_window.statusbar.showMessage(f"Saving Library...")
        start_time = time.time()
        fn = self.lib.save_library_backup_to_disk()
        end_time = time.time()
        self.main_window.statusbar.showMessage(
            f'Library Backup Saved at: "{self.lib.library_dir / TS_FOLDER_NAME / BACKUP_FOLDER_NAME / fn}" ({format_timespan(end_time - start_time)})'
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
                self.lib.add_tag(panel.build_tag()),
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
        self.modal.saved.connect(
            lambda: (
                panel.save(),
                self.filter_items(),  # type: ignore
            )
        )
        self.modal.show()

    def add_new_files_callback(self):
        """Run when user initiates adding new files to the Library."""
        iterator = FunctionIterator(self.lib.refresh_dir)
        pw = ProgressWidget(
            window_title="Refreshing Directories",
            label_text="Scanning Directories for New Files...\nPreparing...",
            cancel_button_text=None,
            minimum=0,
            maximum=0,
        )
        pw.show()
        iterator.value.connect(lambda x: pw.update_progress(x + 1))
        iterator.value.connect(
            lambda x: pw.update_label(
                f'Scanning Directories for New Files...\n{x + 1} File{"s" if x + 1 != 1 else ""} Searched, {len(self.lib.files_not_in_library)} New Files Found'
            )
        )
        r = CustomRunnable(lambda: iterator.run())
        # vvv This one runs the macros when adding new files to the library.
        r.done.connect(
            lambda: (
                pw.hide(),
                pw.deleteLater(),  # type: ignore
                self.add_new_files_runnable(),
            )
        )
        QThreadPool.globalInstance().start(r)

    # def runnable(self, pb:QProgressDialog):
    # 	for i in self.lib.refresh_dir():
    # 		pb.setLabelText(f'Scanning Directories for New Files...\n{i} File{"s" if i != 1 else ""} Searched, {len(self.lib.files_not_in_library)} New Files Found')

    def add_new_files_runnable(self):
        """
        Threaded method that adds any known new files to the library and
        initiates running default macros on them.
        """
        # logger.info(f'Start ANF: {QThread.currentThread()}')
        new_ids: list[int] = self.lib.add_new_files_as_entries()
        # pb = QProgressDialog(f'Running Configured Macros on 1/{len(new_ids)} New Entries', None, 0,len(new_ids))
        # pb.setFixedSize(432, 112)
        # pb.setWindowFlags(pb.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        # pb.setWindowTitle('Running Macros')
        # pb.setWindowModality(Qt.WindowModality.ApplicationModal)
        # pb.show()

        # r = CustomRunnable(lambda: self.new_file_macros_runnable(pb, new_ids))
        # r.done.connect(lambda: (pb.hide(), pb.deleteLater(), self.filter_items('')))
        # r.run()
        # # QThreadPool.globalInstance().start(r)

        # # logger.info(f'{INFO} Running configured Macros on {len(new_ids)} new Entries...')
        # # self.main_window.statusbar.showMessage(f'Running configured Macros on {len(new_ids)} new Entries...', 3)

        # # pb.hide()

        iterator = FunctionIterator(lambda: self.new_file_macros_runnable(new_ids))
        pw = ProgressWidget(
            window_title="Running Macros on New Entries",
            label_text=f"Running Configured Macros on 1/{len(new_ids)} New Entries",
            cancel_button_text=None,
            minimum=0,
            maximum=0,
        )
        pw.show()
        iterator.value.connect(lambda x: pw.update_progress(x + 1))
        iterator.value.connect(
            lambda x: pw.update_label(
                f"Running Configured Macros on {x + 1}/{len(new_ids)} New Entries"
            )
        )
        r = CustomRunnable(iterator.run)
        r.done.connect(
            lambda: (
                pw.hide(),
                pw.deleteLater(),
                self.filter_items(),  # type: ignore
            )
        )
        QThreadPool.globalInstance().start(r)

    def new_file_macros_runnable(self, new_ids):
        """Threaded method that runs macros on a set of Entry IDs."""
        # sleep(1)
        # logger.info(f'ANFR: {QThread.currentThread()}')
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

    def run_macros(self, name: str, entry_ids: list[int]):
        """Runs a specific Macro on a group of given entry_ids."""
        for id in entry_ids:
            self.run_macro(name, id)

    def run_macro(self, name: str, entry_id: int):
        """Runs a specific Macro on an Entry given a Macro name."""
        entry = self.lib.get_entry(entry_id)
        path = self.lib.library_dir / entry.path / entry.filename
        source = entry.path.parts[0]
        if name == "sidecar":
            logger.error("not implemented")
            """
            self.lib.add_generic_data_to_entry(
                self.core.get_gdl_sidecar(path, source), entry_id
            )
            """

        elif name == "autofill":
            self.run_macro("sidecar", entry_id)
            self.run_macro("build-url", entry_id)
            self.run_macro("match", entry_id)
            self.run_macro("clean-url", entry_id)
            self.run_macro("sort-fields", entry_id)
        elif name == "build-url":
            logger.error("not implemented")
            # data = {"source": self.core.build_url(entry_id, source)}
            # self.lib.add_generic_data_to_entry(data, entry_id)
        elif name == "sort-fields":
            order: list[int] = (
                [0]
                + [1, 2]
                + [9, 17, 18, 19, 20]
                + [8, 7, 6]
                + [4]
                + [3, 21]
                + [10, 14, 11, 12, 13, 22]
                + [5]
            )
            self.lib.sort_fields(entry_id, order)
        elif name == "match":
            logger.error("not implemented")
            # self.core.match_conditions(entry_id)
        # elif name == 'scrape':
        # 	self.core.scrape(entry_id)
        elif name == "clean-url":
            # entry = self.lib.get_entry_from_index(entry_id)
            if entry.fields:
                for i, field in enumerate(entry.fields, start=0):
                    if self.lib.get_field_attr(field, "type") == "text_line":
                        self.lib.update_entry_field(
                            entry_id=entry_id,
                            field_index=i,
                            content=strip_web_protocol(
                                self.lib.get_field_attr(field, "content")
                            ),
                            mode="replace",
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

        sb: QScrollArea = self.main_window.scrollArea
        sb_pos = sb.verticalScrollBar().value()
        if page_id is not None:
            page_index = page_id
        else:
            page_index = self.filter.page_index + delta

        self.update_filter(page_index=page_index)
        self.filter_items()

    def purge_item_from_navigation(self, idx: int):
        logger.error("not implemented")
        # TODO - types here are ambiguous
        return
        for i, frame in enumerate(self.nav_frames, start=0):
            while idx in frame.contents:
                logger.info(f"Removing {id} from nav stack frame {i}")
                frame.contents.remove((type, id))

        for i, key in enumerate(self.frame_dict.keys(), start=0):
            for frame in self.frame_dict[key]:
                while (type, id) in frame:
                    logger.info(f"Removing {id} from frame dict item {i}")
                    frame.remove((type, id))

        while idx in self.selected:
            logger.info(f"Removing {idx} from frame selected")
            self.selected.remove(idx)

    def _init_thumb_grid(self):
        # logger.info('Initializing Thumbnail Grid...')
        layout = FlowLayout()
        layout.setGridEfficiency(True)
        # layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(min(self.thumb_size // 10, 12))
        # layout = QHBoxLayout()
        # layout.setSizeConstraint(QLayout.SizeConstraint.SetMaximumSize)
        # layout = QListView()
        # layout.setViewMode(QListView.ViewMode.IconMode)

        for _ in range(self.filter.page_size):
            item_thumb = ItemThumb(
                None, self.lib, self.preview_panel, (self.thumb_size, self.thumb_size)
            )
            layout.addWidget(item_thumb)
            self.item_thumbs.append(item_thumb)

        self.flow_container: QWidget = QWidget()
        self.flow_container.setObjectName("flowContainer")
        self.flow_container.setLayout(layout)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sa: QScrollArea = self.main_window.scrollArea
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sa.setWidgetResizable(True)
        sa.setWidget(self.flow_container)

    def select_item(self, grid_index: int, append: bool, bridge: bool):
        """Select one or more items in the Thumbnail Grid."""
        logger.info(
            "selecting item", grid_index=grid_index, append=append, bridge=bridge
        )
        if append:
            if grid_index not in self.selected:
                self.selected.append(grid_index)
                self.item_thumbs[grid_index].thumb_button.set_selected(True)
            else:
                self.selected.remove(grid_index)
                self.item_thumbs[grid_index].thumb_button.set_selected(False)

        elif bridge and self.selected:
            last_index = self.selected[-1]
            current_index = grid_index

            if last_index < current_index:
                index_range = range(last_index, current_index + 1)
            else:
                index_range = range(current_index, last_index + 1)

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
                    self.preview_panel.set_tags_updated_slot(it.update_badges)

        self.set_macro_menu_viability()
        self.preview_panel.update_widgets()

    def set_macro_menu_viability(self):
        if not self.selected:
            self.autofill_action.setDisabled(True)
            self.sort_fields_action.setDisabled(True)
        else:
            self.autofill_action.setDisabled(False)
            self.sort_fields_action.setDisabled(False)

    def update_thumbs(self):
        """Updates search thumbnails."""
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

        # use zip_longest for self.frame_content and self.item_thumbs
        for idx, (entry, item_thumb) in enumerate(
            zip_longest(self.frame_content, self.item_thumbs)
        ):
            # if self.nav_frames[self.cur_frame_idx].contents[i][0] == ItemType.ENTRY:
            if not entry or not item_thumb:
                break

            filepath = self.lib.library_dir / entry.path
            item_thumb = self.item_thumbs[idx]
            item_thumb.set_mode(ItemType.ENTRY)
            self.thumb_job_queue.put(
                (
                    item_thumb.renderer.render,
                    (sys.float_info.max, "", base_size, ratio, True, True),
                )
            )

            item_thumb.set_item_id(entry)
            # item_thumb.assign_archived(entry.has_tag(self.lib, TAG_ARCHIVED))
            # item_thumb.assign_favorite(entry.has_tag(self.lib, TAG_FAVORITE))
            # ctrl_down = True if QGuiApplication.keyboardModifiers() else False
            # TODO: Change how this works. The click function
            # for collations a few lines down should NOT be allowed during modifier keys.
            item_thumb.update_clickable(
                clickable=(
                    lambda checked=False, idx=idx: self.select_item(
                        idx,
                        append=(
                            QGuiApplication.keyboardModifiers()
                            == Qt.KeyboardModifier.ControlModifier
                        ),
                        bridge=(
                            QGuiApplication.keyboardModifiers()
                            == Qt.KeyboardModifier.ShiftModifier
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

    def update_badges(self):
        logger.info("ts_qt update_badges")
        for i, item_thumb in enumerate(self.item_thumbs, start=0):
            item_thumb.update_badges()

    def filter_items(self, filter: FilterState | None = None) -> None:
        assert self.lib.engine

        self.filter = filter or self.filter

        self.main_window.statusbar.showMessage(
            f'Searching Library: "{self.filter.summary}"'
        )
        self.main_window.statusbar.repaint()
        start_time = time.time()

        query_count, page_items = self.lib.search_library(self.filter)

        logger.info("items to render", count=len(page_items))

        end_time = time.time()
        if self.filter.summary:
            self.main_window.statusbar.showMessage(
                f'{query_count} Results Found for "{self.filter.summary}" ({format_timespan(end_time - start_time)})'
            )
        else:
            self.main_window.statusbar.showMessage(
                f"{query_count} Results ({format_timespan(end_time - start_time)})"
            )

        # update page content
        self.frame_content = page_items
        self.update_thumbs()

        # update pagination
        pages_count = math.ceil(query_count / self.filter.page_size)
        self.main_window.pagination.update_buttons(
            pages_count, self.filter.page_index, emit=False
        )

    def set_search_type(self, mode: SearchMode = SearchMode.AND):
        self.filter_items(
            FilterState(
                search_mode=mode,
                name=self.main_window.searchField.text(),
            )
        )

    def remove_recent_library(self, item_key: str):
        self.settings.beginGroup(SettingItems.LIBS_LIST)
        self.settings.remove(item_key)
        self.settings.endGroup()
        self.settings.sync()

    def update_libs_list(self, path: Path | str):
        """add library to list in SettingItems.LIBS_LIST"""
        ITEMS_LIMIT = 5
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

        for item_key, item_value in all_libs_list[:ITEMS_LIMIT]:
            self.settings.setValue(item_key, item_value)

        self.settings.endGroup()
        self.settings.sync()

    def open_library(self, path: Path | str):
        """Opens a TagStudio library."""
        open_message: str = f'Opening Library "{str(path)}"...'
        self.main_window.landing_widget.set_status_label(open_message)
        self.main_window.statusbar.showMessage(open_message, 3)
        self.main_window.repaint()

        # previous library is opened
        if self.lib.library_dir:
            self.save_library()

        self.lib.open_library(path)
        # TODO - make this call optional
        self.add_new_files_callback()

        self.update_libs_list(path)
        title_text = f"{self.base_title} - Library '{self.lib.library_dir}'"
        self.main_window.setWindowTitle(title_text)

        self.selected.clear()
        self.preview_panel.update_widgets()

        # page (re)rendering, extract eventually
        self.filter_items()

        self.main_window.toggle_landing_page(False)
