# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import enum
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import structlog
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
from src.qt.widgets.progress import ProgressWidget

if TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver

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
        self.setWindowTitle("Conflicting File(s)")  # TODO translate
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(500, 400)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 6, 6, 6)

        self.desc_widget = QLabel()
        self.desc_widget.setObjectName("descriptionLabel")
        self.desc_widget.setWordWrap(True)
        self.desc_widget.setText(
            "The following files have filenames already exist in the library"
        )  # TODO translate
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

        self.skip_button = QPushButton()
        self.skip_button.setText("&Skip")  # TODO translate
        self.skip_button.setDefault(True)
        self.skip_button.clicked.connect(lambda: self.begin_transfer(DuplicateChoice.SKIP))
        self.button_layout.addWidget(self.skip_button)

        self.overwrite_button = QPushButton()
        self.overwrite_button.setText("&Overwrite")  # TODO translate
        self.overwrite_button.clicked.connect(
            lambda: self.begin_transfer(DuplicateChoice.OVERWRITE)
        )
        self.button_layout.addWidget(self.overwrite_button)

        self.rename_button = QPushButton()
        self.rename_button.setText("&Rename")  # TODO translate
        self.rename_button.clicked.connect(lambda: self.begin_transfer(DuplicateChoice.RENAME))
        self.button_layout.addWidget(self.rename_button)

        self.cancel_button = QPushButton()
        self.cancel_button.setText("&Cancel")  # TODO translate
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

        self.collect_files_to_import(urls)

        if len(self.duplicate_files) > 0:
            self.ask_duplicates_choice()
        else:
            self.begin_transfer()

    def collect_files_to_import(self, urls: list[QUrl]):
        """Collect one or more files from drop event urls."""
        for url in urls:
            if not url.isLocalFile():
                continue

            file = Path(url.toLocalFile())

            if file.is_dir():
                for f in file.glob("**/*"):
                    if f.is_dir():
                        continue

                    self.files.append(f)
                    if (self.driver.lib.library_dir / self._get_relative_path(file)).exists():
                        self.duplicate_files.append(f)

                self.dirs_in_root.append(file.parent)
            else:
                self.files.append(file)

                if file.parent not in self.dirs_in_root:
                    self.dirs_in_root.append(
                        file.parent
                    )  # to create relative path of files not in folder

                if (Path(self.driver.lib.library_dir) / file.name).exists():
                    self.duplicate_files.append(file)

    def ask_duplicates_choice(self):
        """Display the message widgeth with a list of the duplicated files."""
        self.desc_widget.setText(
            f"The following {len(self.duplicate_files)} file(s) have filenames already exist in the library."  # noqa: E501
        )  # TODO translate

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
            text = f"Importing New Files...\n{x[0] + 1} File{'s' if x[0] + 1 != 1 else ''} Imported."  # TODO translate
            if self.choice:
                text += f" {x[1]} {self.choice.value}"

            return text

        pw = ProgressWidget(
            window_title="Import Files",  # TODO translate
            label_text="Importing New Files...",  # TODO translate
            cancel_button_text=None,
            minimum=0,
            maximum=len(self.files),
        )

        pw.from_iterable_function(
            self.copy_files,
            displayed_text,
            self.driver.add_new_files_callback,
            self.deleteLater,
        )

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

            (self.driver.lib.library_dir / dest_file).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(file, self.driver.lib.library_dir / dest_file)

            file_count += 1
            yield [file_count, duplicated_files_progress]

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

        while (self.driver.lib.library_dir / filepath).exists():
            filepath = filepath.with_name(
                o_filename[:dot_idx] + f" ({index})" + o_filename[dot_idx:]
            )
            index += 1
        return filepath.name
