# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import enum
import mimetypes
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, override

import requests
import structlog
from PySide6 import QtCore, QtGui
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListView,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from tagstudio.core.utils.types import unwrap
from tagstudio.qt.mixed.progress_bar import ProgressWidget
from tagstudio.qt.translations import Translations

if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class DuplicateChoice(enum.StrEnum):
    SKIP = "Skipped"
    OVERWRITE = "Overwritten"
    RENAME = "Renamed"
    CANCEL = "Cancelled"


class DropImportModal(QWidget):
    DUPE_NAME_LIMT: int = 5

    def __init__(self, driver: "QtDriver"):
        super().__init__()

        self.driver: QtDriver = driver

        # Widget ======================
        self.setWindowTitle(Translations["drop_import.title"])
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(500, 400)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 6, 6, 6)

        self.desc_widget = QLabel()
        self.desc_widget.setObjectName("descriptionLabel")
        self.desc_widget.setWordWrap(True)
        self.desc_widget.setText(Translations["drop_import.description"])
        self.desc_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Duplicate File List ========
        self.list_view = QListView()
        self.model = QStandardItemModel()
        self.list_view.setModel(self.model)

        # Buttons ====================
        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(6, 6, 6, 6)
        self.button_layout.addStretch(1)

        self.skip_button = QPushButton(Translations["generic.skip_alt"])
        self.skip_button.setDefault(True)
        self.skip_button.clicked.connect(lambda: self.begin_transfer(DuplicateChoice.SKIP))
        self.button_layout.addWidget(self.skip_button)

        self.overwrite_button = QPushButton(Translations["generic.overwrite_alt"])
        self.overwrite_button.clicked.connect(
            lambda: self.begin_transfer(DuplicateChoice.OVERWRITE)
        )
        self.button_layout.addWidget(self.overwrite_button)

        self.rename_button = QPushButton(Translations["generic.rename_alt"])
        self.rename_button.clicked.connect(lambda: self.begin_transfer(DuplicateChoice.RENAME))
        self.button_layout.addWidget(self.rename_button)

        self.cancel_button = QPushButton(Translations["generic.cancel_alt"])
        self.cancel_button.clicked.connect(lambda: self.begin_transfer(DuplicateChoice.CANCEL))
        self.button_layout.addWidget(self.cancel_button)

        # Layout =====================
        self.root_layout.addWidget(self.desc_widget)
        self.root_layout.addWidget(self.list_view)
        self.root_layout.addWidget(self.button_container)

    def import_urls(self, urls: list[QUrl]):
        """Add a colleciton of urls to the library."""
        self.files: list[Path] = []
        self.dirs_in_root: list[Path] = []
        self.duplicate_files: list[Path] = []

        files: list[Path] = []

        self.temp_dirs: list[tempfile.TemporaryDirectory] = []
        for url in urls:
            if url.scheme() in ("http", "https"):
                if (file := self.save_web_file(url)) is not None:
                    files.append(file)
            elif url.isLocalFile():
                files.append(Path(url.toLocalFile()))
            else:
                logger.warning("Unsupported URL scheme", url=url.toString(), scheme=url.scheme())

        self.collect_local_files_to_import(files)

        if len(self.duplicate_files) > 0:
            self.ask_duplicates_choice()
        else:
            self.begin_transfer()

    def collect_local_files_to_import(self, files: list[Path]):
        """Collect one or more files from drop event urls."""
        for file in files:
            if file.is_dir():
                for f in file.glob("**/*"):
                    if f.is_dir():
                        continue

                    self.files.append(f)
                    if (
                        unwrap(self.driver.lib.library_dir) / self._get_relative_path(file)
                    ).exists():
                        self.duplicate_files.append(f)

                self.dirs_in_root.append(file.parent)
            else:
                self.files.append(file)

                if file.parent not in self.dirs_in_root:
                    self.dirs_in_root.append(
                        file.parent
                    )  # to create relative path of files not in folder

                if (Path(unwrap(self.driver.lib.library_dir)) / file.name).exists():
                    self.duplicate_files.append(file)

    def ask_duplicates_choice(self):
        """Display the message widgeth with a list of the duplicated files."""
        self.desc_widget.setText(
            Translations["drop_import.duplicates_choice.singular"]
            if len(self.duplicate_files) == 1
            else Translations.format(
                "drop_import.duplicates_choice.plural", count=len(self.duplicate_files)
            )
        )

        self.model.clear()
        for dupe in self.duplicate_files:
            item = QStandardItem(str(self._get_relative_path(dupe)))
            item.setEditable(False)
            self.model.appendRow(item)

        self.driver.main_window.raise_()
        self.show()

    def begin_transfer(self, choice: DuplicateChoice | None = None):
        """Display a progress bar and begin copying files into library."""
        self.hide()
        self.choice: DuplicateChoice | None = choice
        logger.info("duplicated choice selected", choice=self.choice)
        if self.choice == DuplicateChoice.CANCEL:
            return

        def displayed_text(x):
            return Translations.format(
                "drop_import.progress.label.singular"
                if x[0] + 1 == 1
                else "drop_import.progress.label.plural",
                count=x[0] + 1,
                suffix=f" {x[1]} {self.choice.value}" if self.choice else "",
            )

        pw = ProgressWidget(
            cancel_button_text=None,
            minimum=0,
            maximum=len(self.files),
        )
        pw.setWindowTitle(Translations["drop_import.progress.window_title"])
        pw.update_label(Translations["drop_import.progress.label.initial"])

        pw.from_iterable_function(
            self.copy_files,
            displayed_text,
            self.driver.add_new_files_callback,
            self.deleteLater,
            self.cleanup_temp_dirs,
        )

    def cleanup_temp_dirs(self):
        """Cleanup all temporary directories created for downloaded files."""
        for temp_dir in self.temp_dirs:
            temp_dir.cleanup()
        self.temp_dirs.clear()

    def copy_files(self):
        """Copy files from original location to the library directory."""
        file_count = 0
        duplicated_files_progress = 0
        for file in self.files:
            if file.is_dir():
                continue

            dest_file = self._get_relative_path(file)

            if file in self.duplicate_files:
                duplicated_files_progress += 1
                if self.choice == DuplicateChoice.SKIP:
                    file_count += 1
                    continue
                elif self.choice == DuplicateChoice.RENAME:
                    new_name = self._get_renamed_duplicate_filename(dest_file)
                    dest_file = dest_file.with_name(new_name)

            (unwrap(self.driver.lib.library_dir) / dest_file).parent.mkdir(
                parents=True, exist_ok=True
            )
            shutil.copyfile(file, unwrap(self.driver.lib.library_dir) / dest_file)

            file_count += 1
            yield [file_count, duplicated_files_progress]

    def save_web_file(self, url: QUrl) -> Path | None:
        with requests.get(url.toString(), stream=True) as response:
            if not response.ok:
                logger.error(
                    "Failed to download URL", url=url.toString(), status_code=response.status_code
                )
                return None

            cd = response.headers.get("Content-Disposition")
            if cd is None or not (cd.startswith("attachment;") or cd.startswith("inline;")):
                logger.error("URL does not point to a downloadable file", url=url.toString())
                return None

            # Save in separate temp dirs to avoid filename conflicts, since those are
            # managed later by `self.ask_duplicates_choice()`.
            temp_dir = tempfile.TemporaryDirectory()

            if "filename=" in cd:
                fname = cd.split("filename=")[-1].split(";")[0].strip('"')
                logger.info("Filename from Content-Disposition header", filename=fname)
            else:
                to_guess = response.headers.get("Content-Type", "application/octet-stream")
                ext = mimetypes.guess_extension(to_guess)
                if ext is None:
                    logger.warning(
                        "Could not determine file extension for URL",
                        url=url.toString(),
                        content_type=to_guess,
                    )
                    ext = ".bin"
                fname = f"downloaded_file_{len(self.temp_dirs)}{ext}"
                logger.info("Filename not available, using generated filename", filename=fname)

            out_path = Path(temp_dir.name) / fname
            logger.info("Downloading file from URL", url=url.toString(), output_path=str(out_path))
            with open(out_path, "wb") as fd:
                for chunk in response.iter_content(chunk_size=8192):
                    fd.write(chunk)

            self.temp_dirs.append(temp_dir)

            return out_path

    def _get_relative_path(self, path: Path) -> Path:
        for dir in self.dirs_in_root:
            if path.is_relative_to(dir):
                return path.relative_to(dir)
        return Path(path.name)

    def _get_renamed_duplicate_filename(self, filepath: Path) -> str:
        index = 2
        o_filename = filepath.name

        try:
            dot_idx = o_filename.index(".")
        except ValueError:
            dot_idx = len(o_filename)

        while (unwrap(self.driver.lib.library_dir) / filepath).exists():
            filepath = filepath.with_name(
                o_filename[:dot_idx] + f" ({index})" + o_filename[dot_idx:]
            )
            index += 1
        return filepath.name

    @override
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # noqa N802
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.cancel_button.click()
        else:  # Other key presses
            pass
        return super().keyPressEvent(event)
