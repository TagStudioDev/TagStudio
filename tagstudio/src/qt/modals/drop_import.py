from pathlib import Path
import shutil
import typing
import logging

from PySide6.QtGui import QDropEvent, QDragEnterEvent, QDragMoveEvent
from PySide6.QtWidgets import QMessageBox

if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver

logging.basicConfig(format="[DROP IMPORT] %(message)s", level=logging.INFO)


def dropEvent(driver: "QtDriver", event: QDropEvent):
    if not event.mimeData().hasUrls():
        return

    import_files(driver, event.mimeData().urls())


def dragEnterEvent(event: QDragEnterEvent):
    if event.mimeData().hasUrls():
        event.accept()
    else:
        event.ignore()


def dragMoveEvent(event: QDragMoveEvent):
    if event.mimeData().hasUrls():
        event.accept()
    else:
        event.ignore()


def import_files(driver: "QtDriver", urls):
    files: list[Path] = []
    dirs_in_root: list[Path] = []
    duplicate_files: list[Path] = []

    for url in urls:
        if not url.isLocalFile():
            continue

        file = Path(url.toLocalFile())

        if file.is_dir():
            files += get_files_in_folder(file)
            dirs_in_root.append(file.parent)

            dupes = get_files_exists_in_library(
                dirs_in_root, driver.lib.library_dir, file
            )
            duplicate_files += dupes
        else:
            files.append(file)

            if file.parent not in dirs_in_root:
                dirs_in_root.append(
                    file.parent
                )  # to create relative path of files not in folder

            if (Path(driver.lib.library_dir) / file.name).exists():
                duplicate_files.append(file)

    ret = -1

    if len(duplicate_files) > 0:
        ret = duplicates_choice(dirs_in_root, duplicate_files)

        if ret == 3:  # cancel
            return

    for file in files:
        if file.is_dir():
            continue

        dest_file = get_relativ_path(dirs_in_root, file)

        if file in duplicate_files:
            if ret == 0:  # skip duplicates
                continue

            if ret == 2:  # rename
                new_name = get_renamed_duplicate_filename(
                    Path(driver.lib.library_dir), dest_file
                )
                dest_file = dest_file.with_name(new_name)
                driver.lib.files_not_in_library.append(dest_file)
        else:  # override is simply copying but not adding a new entry
            driver.lib.files_not_in_library.append(dest_file)

        (driver.lib.library_dir / dest_file).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(file, driver.lib.library_dir / dest_file)

    driver.add_new_files_runnable()


def duplicates_choice(dirs_in_root: list[Path], duplicate_files: list[Path]) -> int:
    msgBox = QMessageBox()
    msgBox.setText(
        f"The files  {', '.join(map(lambda path: str(path),get_relativ_paths(dirs_in_root, duplicate_files)))}  have filenames that already exist in the library folder."
    )
    msgBox.addButton("Skip", QMessageBox.ButtonRole.YesRole)
    msgBox.addButton("Override", QMessageBox.ButtonRole.DestructiveRole)
    msgBox.addButton("Rename", QMessageBox.ButtonRole.DestructiveRole)
    msgBox.addButton("Cancel", QMessageBox.ButtonRole.NoRole)
    return msgBox.exec()


def get_renamed_duplicate_filename(path: Path, filePath: Path) -> str:
    index = 2
    o_filename = filePath.name
    dot_idx = o_filename.index(".")
    while (path / filePath).exists():
        filePath = filePath.with_name(
            o_filename[:dot_idx] + f" ({index})" + o_filename[dot_idx:]
        )
        index += 1
    return filePath.name


def get_files_in_folder(path: Path) -> list[Path]:
    files = []
    for file in path.glob("**/*"):
        files.append(file)
    return files


def get_files_exists_in_library(
    dirs_in_root: list[Path], lib_dir: str, path: Path
) -> list[Path]:
    exists: list[Path] = []
    if not path.is_dir():
        return exists

    files = get_files_in_folder(path)
    for file in files:
        if file.is_dir():
            exists += get_files_exists_in_library(dirs_in_root, lib_dir, file)
        elif (lib_dir / get_relativ_path(dirs_in_root, file)).exists():
            exists.append(file)
    return exists


def get_relativ_paths(roots: list[Path], paths: list[Path]) -> list[Path]:
    relativ_paths = []
    for file in paths:
        relativ_paths.append(get_relativ_path(roots, file))
    return relativ_paths


def get_relativ_path(roots: list[Path], path: Path) -> Path:
    for dir in roots:
        if path.is_relative_to(dir):
            return path.relative_to(dir)
    return path.name
