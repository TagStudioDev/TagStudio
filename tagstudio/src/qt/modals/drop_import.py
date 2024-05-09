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
                msgBox.addButton("Cancel", QMessageBox.ButtonRole.NoRole)
                ret = msgBox.exec()

                if ret == 2:
                    return

            for url in urls:
                if ret == 0 and url in duplicate_filesnames:
                    continue
                shutil.copyfile(
                    url.toLocalFile(), driver.lib.library_dir + "/" + url.fileName()
                )
                if ret == 1 and url in duplicate_filesnames:
                    continue
                driver.lib.files_not_in_library.append(url.fileName())

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
