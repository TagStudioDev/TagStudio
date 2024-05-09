import os
import shutil
import typing

from PySide6.QtGui import QDropEvent, QDragEnterEvent, QDragMoveEvent
from PySide6.QtWidgets import QMessageBox

if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver


def dropEvent(driver: "QtDriver", event: QDropEvent):
    if event.mimeData().hasUrls():
        if event.mimeData().urls()[0].isLocalFile():
            urls = event.mimeData().urls()
            duplicate_filesnames = []
            for url in urls:
                if os.path.exists(driver.lib.library_dir + "/" + url.fileName()):
                    duplicate_filesnames.append(url)

            ret = -1

            if len(duplicate_filesnames) > 0:
                msgBox = QMessageBox()
                msgBox.setText(
                    f"The files  {", ".join(map(lambda url:url.fileName(),duplicate_filesnames))}  have filenames that already exist in the library folder."
                )
                msgBox.addButton("Skip", QMessageBox.ButtonRole.YesRole)
                msgBox.addButton("Override", QMessageBox.ButtonRole.DestructiveRole)
                msgBox.addButton("Rename", QMessageBox.ButtonRole.DestructiveRole)
                msgBox.addButton("Cancel", QMessageBox.ButtonRole.NoRole)
                ret = msgBox.exec()

                if ret == 3:  # cancel
                    return

            for url in urls:
                filename = url.fileName()

                if url in duplicate_filesnames:
                    if ret == 0:  # skip duplicates
                        continue
                    if ret == 1:  # only override file contents of duplicates
                        shutil.copyfile(
                            url.toLocalFile(), driver.lib.library_dir + "/" + filename
                        )
                        continue
                    if ret == 2:  # rename duplicates
                        index = 2
                        o_filename = url.fileName()
                        dot_idx = o_filename.index(".")
                        while os.path.exists(driver.lib.library_dir + "/" + filename):
                            filename = (
                                o_filename[:dot_idx]
                                + f" ({index})"
                                + o_filename[dot_idx:]
                            )
                            index += 1

                shutil.copyfile(
                    url.toLocalFile(), driver.lib.library_dir + "/" + filename
                )
                driver.lib.files_not_in_library.append(filename)

            driver.add_new_files_runnable()


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
