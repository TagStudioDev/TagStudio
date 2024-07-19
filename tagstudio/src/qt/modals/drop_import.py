# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from pathlib import Path
import shutil
import typing

from PySide6.QtCore import QThreadPool
from PySide6.QtGui import QDropEvent, QDragEnterEvent, QDragMoveEvent
from PySide6.QtWidgets import QMessageBox
from src.qt.widgets.progress import ProgressWidget
from src.qt.helpers.custom_runnable import CustomRunnable
from src.qt.helpers.function_iterator import FunctionIterator

if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver

import logging


class DropImport:
    def __init__(self, driver: "QtDriver"):
        self.driver = driver

    def dropEvent(self, event: QDropEvent):
        if (
            event.source() is self.driver
        ):  # change that if you want to drop something originating from tagstudio, for moving or so
            return

        if not event.mimeData().hasUrls():
            return

        self.urls = event.mimeData().urls()
        self.import_files()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            logging.info(self.driver.selected)
            event.ignore()

    def import_files(self):
        self.files: list[Path] = []
        self.dirs_in_root: list[Path] = []
        self.duplicate_files: list[Path] = []

        def displayed_text(x):
            text = f"Searching New Files...\n{x[0]+1} File{'s' if x[0]+1 != 1 else ''} Found."
            if x[1] == 0:
                return text
            return text + f" {x[1]} Already exist in the library folders"

        create_progress_bar(
            self.collect_files_to_import,
            "Searching Files",
            "Searching New Files...\nPreparing...",
            displayed_text,
            self.ask_user,
        )

    def collect_files_to_import(self):
        for url in self.urls:
            if not url.isLocalFile():
                continue

            file = Path(url.toLocalFile())

            if file.is_dir():
                for f in self.get_files_in_folder(file):
                    if f.is_dir():
                        continue
                    self.files.append(f)
                    if (
                        self.driver.lib.library_dir / self.get_relative_path(file)
                    ).exists():
                        self.duplicate_files.append(f)
                    yield [len(self.files), len(self.duplicate_files)]

                self.dirs_in_root.append(file.parent)
            else:
                self.files.append(file)

                if file.parent not in self.dirs_in_root:
                    self.dirs_in_root.append(
                        file.parent
                    )  # to create relative path of files not in folder

                if (Path(self.driver.lib.library_dir) / file.name).exists():
                    self.duplicate_files.append(file)

                yield [len(self.files), len(self.duplicate_files)]

    def copy_files(self):
        fileCount = 0
        duplicated_files_progress = 0
        for file in self.files:
            if file.is_dir():
                continue

            dest_file = self.get_relative_path(file)

            if file in self.duplicate_files:
                duplicated_files_progress += 1
                if self.choice == 0:  # skip duplicates
                    continue

                if self.choice == 2:  # rename
                    new_name = self.get_renamed_duplicate_filename_in_lib(dest_file)
                    dest_file = dest_file.with_name(new_name)
                    self.driver.lib.files_not_in_library.append(dest_file)
            else:  # override is simply copying but not adding a new entry
                self.driver.lib.files_not_in_library.append(dest_file)

            (self.driver.lib.library_dir / dest_file).parent.mkdir(
                parents=True, exist_ok=True
            )
            shutil.copyfile(file, self.driver.lib.library_dir / dest_file)

            fileCount += 1
            yield [fileCount, duplicated_files_progress]

    def ask_user(self):
        self.choice = -1

        if len(self.duplicate_files) > 0:
            self.choice = self.duplicates_choice()

            if self.choice == 3:  # cancel
                return

        def displayed_text(x):
            dupes_choice_text = (
                "Skipped"
                if self.choice == 0
                else ("Overridden" if self.choice == 1 else "Renamed")
            )

            text = f"Importing New Files...\n{x[0]+1} File{'s' if x[0]+1 != 1 else ''} Imported."
            if x[1] == 0:
                return text
            return text + f" {x[1]} {dupes_choice_text}"

        create_progress_bar(
            self.copy_files,
            "Import Files",
            "Importing New Files...\nPreparing...",
            displayed_text,
            self.driver.add_new_files_runnable,
            len(self.files),
        )

    def duplicates_choice(self) -> int:
        display_limit: int = 5
        msgBox = QMessageBox()
        msgBox.setWindowTitle(
            f"File Conflict{'s' if len(self.duplicate_files) > 1 else ''}"
        )

        dupes_to_show = self.duplicate_files
        if len(self.duplicate_files) > display_limit:
            dupes_to_show = dupes_to_show[0:display_limit]

        dupes_str = "\n    ".join(map(lambda path: str(path), dupes_to_show))
        dupes_more = (
            f"\nand {len(self.duplicate_files)-display_limit} more "
            if len(self.duplicate_files) > display_limit
            else "\n"
        )

        msgBox.setText(
            f"The following files:\n    {dupes_str}{dupes_more}have filenames that already exist in the library folder."
        )
        msgBox.addButton("Skip", QMessageBox.ButtonRole.YesRole)
        msgBox.addButton("Override", QMessageBox.ButtonRole.DestructiveRole)
        msgBox.addButton("Rename", QMessageBox.ButtonRole.DestructiveRole)
        msgBox.addButton("Cancel", QMessageBox.ButtonRole.NoRole)
        return msgBox.exec()

    def get_files_exists_in_library(self, path: Path) -> list[Path]:
        exists: list[Path] = []
        if not path.is_dir():
            return exists

        files = self.get_files_in_folder(path)
        for file in files:
            if file.is_dir():
                exists += self.get_files_exists_in_library(file)
            elif (self.driver.lib.library_dir / self.get_relative_path(file)).exists():
                exists.append(file)
        return exists

    def get_relative_paths(self, paths: list[Path]) -> list[Path]:
        relative_paths = []
        for file in paths:
            relative_paths.append(self.get_relative_path(file))
        return relative_paths

    def get_relative_path(self, path: Path) -> Path:
        for dir in self.dirs_in_root:
            if path.is_relative_to(dir):
                return path.relative_to(dir)
        return Path(path.name)

    def get_files_in_folder(self, path: Path) -> list[Path]:
        files = []
        for file in path.glob("**/*"):
            files.append(file)
        return files

    def get_renamed_duplicate_filename_in_lib(self, filePath: Path) -> str:
        index = 2
        o_filename = filePath.name
        dot_idx = o_filename.index(".")
        while (self.driver.lib.library_dir / filePath).exists():
            filePath = filePath.with_name(
                o_filename[:dot_idx] + f" ({index})" + o_filename[dot_idx:]
            )
            index += 1
        return filePath.name


def create_progress_bar(
    function, title: str, text: str, update_label_callback, done_callback, max=0
):
    iterator = FunctionIterator(function)
    pw = ProgressWidget(
        window_title=title,
        label_text=text,
        cancel_button_text=None,
        minimum=0,
        maximum=max,
    )
    pw.show()
    iterator.value.connect(lambda x: pw.update_progress(x[0] + 1))
    iterator.value.connect(lambda x: pw.update_label(update_label_callback(x)))
    r = CustomRunnable(lambda: iterator.run())
    r.done.connect(lambda: (pw.hide(), done_callback()))  # type: ignore
    QThreadPool.globalInstance().start(r)
