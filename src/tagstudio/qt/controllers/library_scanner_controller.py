from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QWidget

from tagstudio.core.library.refresh import RefreshTracker
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.mixed.progress_bar import ProgressWidget
from tagstudio.qt.mixed.unlinked_entries_modal import UnlinkedEntriesModal
from tagstudio.qt.translations import Translations
from tagstudio.qt.utils.custom_runnable import CustomRunnable
from tagstudio.qt.utils.function_iterator import FunctionIterator

if TYPE_CHECKING:
    from tagstudio.core.library.alchemy.library import Library
    from tagstudio.qt.ts_qt import QtDriver


class LibraryScannerController(QWidget):
    def __init__(self, driver: "QtDriver", lib: "Library"):
        super().__init__()
        self.driver = driver
        self.lib = lib
        self.tracker = RefreshTracker(lib)
        self.unlinked_modal = UnlinkedEntriesModal(self.driver, self)

    @property
    def unlinked_entries_count(self) -> int:
        return self.tracker.missing_files_count

    @property
    def new_files_count(self) -> int:
        return self.tracker.new_files_count

    @property
    def unlinked_paths(self) -> list[Path]:
        return list(self.tracker._missing_paths.keys())

    def _progress_bar(self, pw: ProgressWidget, iterator, on_update, on_finish):
        pw.show()
        iterator = FunctionIterator(iterator)
        iterator.value.connect(on_update)
        r = CustomRunnable(iterator.run)
        r.done.connect(lambda: (pw.hide(), pw.deleteLater(), on_finish()))
        QThreadPool.globalInstance().start(r)

    def scan(self, on_finish=None):
        pw = ScanProgressWidget()

        def on_finish_():
            self.driver.on_library_scan()

            if on_finish is not None:
                on_finish()
            elif self.tracker.missing_files_count > 0:
                self.open_unlinked_view()
            else:
                self.save_new_files()

        library_dir = unwrap(self.lib.library_dir)
        self._progress_bar(
            pw,
            iterator=lambda: self.tracker.refresh_dir(library_dir),
            on_update=lambda i: pw.on_update(i),
            on_finish=on_finish_,
        )

    def open_unlinked_view(self):
        self.unlinked_modal.show()

    def fix_unlinked_entries(self):
        self.tracker.fix_unlinked_entries()
        self.driver.on_library_scan()

    def remove_unlinked_entries(self):
        self.tracker.remove_unlinked_entries()
        self.driver.on_library_scan()

    def save_new_files(self):
        files_to_save = self.tracker.new_files_count
        if files_to_save == 0:
            return

        def on_finish():
            self.driver.on_library_scan()
            self.driver.update_browsing_state()

        pw = SaveNewProgressWidget(files_to_save)
        self._progress_bar(
            pw,
            iterator=self.tracker.save_new_files,
            on_update=lambda i: pw.on_update(i),
            on_finish=on_finish,
        )


class ScanProgressWidget(ProgressWidget):
    def __init__(self):
        super().__init__(
            cancel_button_text=None,
            minimum=0,
            maximum=0,
            window_title=Translations["library.refresh.title"],
            label_text=Translations["library.refresh.scanning_preparing"],
        )

    def on_update(self, files_searched: int):
        self.update_label(
            Translations.format(
                "library.refresh.scanning.singular"
                if files_searched == 1
                else "library.refresh.scanning.plural",
                searched_count=f"{files_searched:n}",
                found_count=0,  # New files are found after scan in single step so no progress
            )
        )


class SaveNewProgressWidget(ProgressWidget):
    def __init__(self, files_to_save: int):
        super().__init__(
            cancel_button_text=None,
            minimum=0,
            maximum=files_to_save,
            window_title=Translations["entries.running.dialog.title"],
            label_text=Translations.format("library.refresh.scanning_preparing", total=0),
        )

    def on_update(self, files_saved: int):
        self.update_progress(files_saved)
        self.update_label(
            Translations.format("entries.running.dialog.new_entries", total=f"{files_saved:n}")
        )
