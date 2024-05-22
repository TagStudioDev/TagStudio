from pathlib import Path
import shutil
import typing

from PySide6.QtCore import QThreadPool,Qt,QMimeData,QUrl
from PySide6.QtGui import QDropEvent, QDragEnterEvent,QImage, QDragMoveEvent,QMouseEvent,QDrag,QDragLeaveEvent
from PySide6.QtWidgets import QMessageBox
from src.qt.widgets import ProgressWidget
from src.qt.helpers import FunctionIterator, CustomRunnable

from ctypes import wintypes,windll

if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver

import logging

class DropImport:
    def __init__(self, driver: "QtDriver"):
        self.driver = driver
    
    def mouseMoveEvent(self,event:QMouseEvent):
        if event.buttons() is not Qt.MouseButton.LeftButton: return
        if len(self.driver.selected) == 0: return
        
        drag = QDrag(self.driver)
        paths = []
        mimedata = QMimeData()
        for selected in  self.driver.selected:
            entry =self.driver.lib.get_entry(selected[1])
            url = QUrl.fromLocalFile(self.driver.lib.library_dir+"/"+entry.path+"/"+entry.filename)
            paths.append(url)
        
        mimedata.setUrls(paths)
        drag.setMimeData(mimedata)
        drag.exec(Qt.DropAction.CopyAction)
    
    def dropEvent(self, event: QDropEvent):
        if event.source() is self.driver: # change that if you want to drop something originating from tagstudio, for moving or so
            return

        if not event.mimeData().hasUrls():
            return

        self.urls = event.mimeData().urls()
        self.import_files()

    def dragLeaveEvent(self,event:QDragLeaveEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

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

        self.start_collection_progress()

    def start_collection_progress(self):
        iterator = FunctionIterator(self.collect_files_to_import)
        pw = ProgressWidget(
            window_title="Searching Files",
            label_text="Searching New Files...\nPreparing...",
            cancel_button_text=None,
            minimum=0,
            maximum=0,
        )
        pw.show()
        iterator.value.connect(lambda x: pw.update_progress(x[0] + 1))
        iterator.value.connect(
            lambda x: pw.update_label(
                f'Searching New Files...\n{x[0]+1} File{"s" if x[0]+1 != 1 else ""} Found. {(f"{x[1]} Already exist in the library folders") if x[1]>0 else ""}'
            )
        )
        r = CustomRunnable(lambda: iterator.run())
        r.done.connect(lambda: (pw.hide(), self.ask_user()))
        QThreadPool.globalInstance().start(r)

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
                        self.driver.lib.library_dir / self.get_relativ_path(file)
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

    def start_copy_progress(self):
        iterator = FunctionIterator(self.copy_files)
        pw = ProgressWidget(
            window_title="Import Files",
            label_text="Importing New Files...\nPreparing...",
            cancel_button_text=None,
            minimum=0,
            maximum=len(self.files),
        )
        pw.show()
        iterator.value.connect(lambda x: pw.update_progress(x[0] + 1))
        dupes_choice_text = (
            "Skipped"
            if self.choice == 0
            else ("Overridden" if self.choice == 1 else "Renamed")
        )
        iterator.value.connect(
            lambda x: pw.update_label(
                f'Importing New Files...\n{x[0]+1} File{"s" if x[0]+1 != 1 else ""} Imported. {(f"{x[1]} {dupes_choice_text}") if x[1]>0 else ""}'
            )
        )
        r = CustomRunnable(lambda: iterator.run())
        r.done.connect(lambda: (pw.hide(), self.driver.add_new_files_runnable()))
        QThreadPool.globalInstance().start(r)

    def copy_files(self):
        fileCount = 0
        duplicated_files_progress = 0
        for file in self.files:
            if file.is_dir():
                continue

            dest_file = self.get_relativ_path(file)

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

        self.start_copy_progress()

    def duplicates_choice(self) -> int:
        msgBox = QMessageBox()
        dupes_to_show = self.duplicate_files
        if len(self.duplicate_files) > 20:
            dupes_to_show = dupes_to_show[0:20]

        msgBox.setText(
            f"The files  {', '.join(map(lambda path: str(path),self.get_relativ_paths(dupes_to_show)))} {(f"and {len(self.duplicate_files)-20} more") if len(self.duplicate_files)>20 else ""}  have filenames that already exist in the library folder."
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
            elif (self.driver.lib.library_dir / self.get_relativ_path(file)).exists():
                exists.append(file)
        return exists

    def get_relativ_paths(self, paths: list[Path]) -> list[Path]:
        relativ_paths = []
        for file in paths:
            relativ_paths.append(self.get_relativ_path(file))
        return relativ_paths

    def get_relativ_path(self, path: Path) -> Path:
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


