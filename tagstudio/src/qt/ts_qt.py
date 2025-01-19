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
from pathlib import Path
from queue import Queue

# this import has side-effect of import PySide resources
import src.qt.resources_rc  # noqa: F401
import structlog
from humanfriendly import format_timespan
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
    QPixmap,
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QLineEdit,
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
from src.qt.modals.drop_import import DropImportModal
from src.qt.modals.tag_database import TagDatabasePanel
from src.qt.resource_manager import ResourceManager
from src.qt.translations import Translations
from src.qt.widgets.item_thumb import BadgeType, ItemThumb
from src.qt.widgets.menu_bar import MenuBar
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

    def open_create_library_modal(self):
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

        self.menu_bar = MenuBar(self.main_window, self.settings, self.lib, self)
        self.menu_bar.create_library_modal_signal.connect(self.open_create_library_modal)
        self.menu_bar.open_library_signal.connect(self.open_library)
        self.menu_bar.backup_library_signal.connect(self.backup_library)
        self.menu_bar.refresh_directories_signal.connect(self.refresh_directories)
        self.menu_bar.close_library_signal.connect(self.close_library)
        self.menu_bar.select_all_items_signal.connect(self.select_all_items)
        self.menu_bar.clear_selection_signal.connect(self.clear_selection)
        self.menu_bar.filter_items_signal.connect(self.filter_items)
        self.menu_bar.tag_database_modal_signal.connect(self.open_tag_database_modal)
        self.menu_bar.show_grid_filenames_signal.connect(self.show_grid_filenames)
        self.menu_bar.autofill_macro_signal.connect(
            lambda: (
                self.run_macros(MacroID.AUTOFILL, self.selected),
                self.preview_panel.update_widgets(),
            )
        )
        self.menu_bar.set_macro_actions_disabled(not self.selected)
        self.main_window.setMenuBar(self.menu_bar)
        self.menu_bar.set_library_actions_disabled(True)

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
        self.preview_panel.update_widgets()

    def show_grid_filenames(self, value: bool):
        for thumb in self.item_thumbs:
            thumb.set_filename_visibility(value)

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

        self.lib.close()
        self.menu_bar.set_library_actions_disabled(True)

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
        if not self.lib.library_dir:
            return
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

    def select_all_items(self):
        """Set the selection to all visible items."""
        self.selected.clear()
        for item in self.item_thumbs:
            if item.mode and item.item_id not in self.selected:
                self.selected.append(item.item_id)
                item.thumb_button.set_selected(True)

        self.menu_bar.set_macro_actions_disabled(not self.selected)
        self.preview_panel.update_widgets()

    def clear_selection(self):
        self.selected.clear()
        for item in self.item_thumbs:
            item.thumb_button.set_selected(False)

        self.menu_bar.set_macro_actions_disabled(not self.selected)
        self.preview_panel.update_widgets()

    def open_tag_database_modal(self):
        self.modal = PanelModal(
            widget=TagDatabasePanel(self.lib),
            done_callback=self.preview_panel.update_widgets,
            has_save=False,
        )
        Translations.translate_with_setter(self.modal.setTitle, "tag_manager.title")
        Translations.translate_with_setter(self.modal.setWindowTitle, "tag_manager.title")
        self.modal.show()

    def refresh_directories(self):
        """Run when user initiates adding new files to the Library."""
        if not self.lib.library_dir:
            return

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

        self.menu_bar.set_macro_actions_disabled(not self.selected)
        self.preview_panel.update_widgets()

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
        self.menu_bar.update_recent_lib_menu()

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
            self.refresh_directories()

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
        self.menu_bar.set_library_actions_disabled(False)
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
