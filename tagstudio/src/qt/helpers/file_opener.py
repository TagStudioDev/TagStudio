# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import logging
import os
import subprocess
import shutil
import sys
import traceback
from pathlib import Path

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, QEvent, QTimer
from PySide6.QtGui import Qt, QEnterEvent, QResizeEvent, QFontMetrics

ERROR = f"[ERROR]"
WARNING = f"[WARNING]"
INFO = f"[INFO]"

logging.basicConfig(format="%(message)s", level=logging.INFO)


def open_file(path: str | Path, file_manager: bool = False):
    """Open a file in the default application or file explorer.

    Args:
            path (str): The path to the file to open.
            file_manager (bool, optional): Whether to open the file in the file manager (e.g. Finder on macOS).
                    Defaults to False.
    """
    _path = str(path)
    logging.info(f"Opening file: {_path}")
    if not os.path.exists(_path):
        logging.error(f"File not found: {_path}")
        return
    try:
        if sys.platform == "win32":
            normpath = os.path.normpath(_path)
            if file_manager:
                command_name = "explorer"
                command_args = '/select,"' + normpath + '"'
                # For some reason, if the args are passed in a list, this will error when the path has spaces, even while surrounded in double quotes
                subprocess.Popen(
                    command_name + command_args,
                    shell=True,
                    close_fds=True,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                    | subprocess.CREATE_BREAKAWAY_FROM_JOB,
                )
            else:
                command_name = "start"
                # first parameter is for title, NOT filepath
                command_args = ["", normpath]
                subprocess.Popen(
                    [command_name] + command_args,
                    shell=True,
                    close_fds=True,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                    | subprocess.CREATE_BREAKAWAY_FROM_JOB,
                )
        else:
            if sys.platform == "darwin":
                command_name = "open"
                command_args = [_path]
                if file_manager:
                    # will reveal in Finder
                    command_args.append("-R")
            else:
                if file_manager:
                    command_name = "dbus-send"
                    # might not be guaranteed to launch default?
                    command_args = [
                        "--session",
                        "--dest=org.freedesktop.FileManager1",
                        "--type=method_call",
                        "/org/freedesktop/FileManager1",
                        "org.freedesktop.FileManager1.ShowItems",
                        f"array:string:file://{_path}",
                        "string:",
                    ]
                else:
                    command_name = "xdg-open"
                    command_args = [_path]
            command = shutil.which(command_name)
            if command is not None:
                subprocess.Popen([command] + command_args, close_fds=True)
            else:
                logging.info(f"Could not find {command_name} on system PATH")
    except:
        traceback.print_exc()


class FileOpenerHelper:
    def __init__(self, filepath: str | Path):
        """Initialize the FileOpenerHelper.

        Args:
                filepath (str): The path to the file to open.
        """
        self.filepath = str(filepath)

    def set_filepath(self, filepath: str | Path):
        """Set the filepath to open.

        Args:
                filepath (str): The path to the file to open.
        """
        self.filepath = str(filepath)

    def open_file(self):
        """Open the file in the default application."""
        open_file(self.filepath)

    def open_explorer(self):
        """Open the file in the default file explorer."""
        open_file(self.filepath, file_manager=True)


class FileOpenerLabel(QLabel):
    def __init__(self, text, parent=None):
        """Initialize the FileOpenerLabel.

        Args:
                text (str): The text to display.
                parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(text, parent)
        self.filepath = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._show_full_path_callback)
        self.font_metrics = QFontMetrics(self.font())

    def setFilePath(self, filepath):
        """Set the filepath to open.

        Args:
                filepath (str): The path to the file to open.
        """
        self.filepath = filepath

    def truncate_filepath(self, filepath):
        path = Path(filepath)
        max_chars = self.width() // self.font_metrics.averageCharWidth()

        if len(str(path)) > max_chars:
            name_size = len(path.name) + 4
            prev = ""

            for parent in reversed(path.parents):
                if len(str(parent)) + name_size > max_chars:
                    if sys.platform == "win32":
                        return f"{prev}\\..\\{path.name}"
                    return f"{prev}/../{path.name}"
                prev = parent
        return str(path)

    def setText(self, text: str):
        if not self.filepath:
            return super().setText(text)

        filepath = Path(text)
        file_str: str = ""
        sep_color: str = "#777777"  # Gray
        for i, part in enumerate(filepath.parts):
            part_ = part.strip(os.path.sep)
            if i == 0:
                file_str += f"{"\u200b".join(part_)}<a style='color: {sep_color}'><b>{os.path.sep}</a></b>"
            elif i != 0 and i != len(filepath.parts) - 1:
                file_str += f"{"\u200b".join(part_)}<a style='color: {sep_color}'><b>{os.path.sep}</b></a>"
            else:
                file_str += f"<b>{"\u200b".join(part_)}</b>"
        return super().setText(file_str)

    def enterEvent(self, event: QEnterEvent) -> None:
        if self.filepath:
            self.timer.start(250)
        return super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        if self.filepath:
            self.timer.stop()
            self.setText(self.truncate_filepath(self.filepath))
        return super().leaveEvent(event)

    def _show_full_path_callback(self):
        self.setText(str(self.filepath))

    def mousePressEvent(self, event):
        """Handle mouse press events.

        On a left click, open the file in the default file explorer. On a right click, show a context menu.

        Args:
                event (QMouseEvent): The mouse press event.
        """
        super().mousePressEvent(event)

        if event.button() == Qt.LeftButton:
            opener = FileOpenerHelper(self.filepath)
            opener.open_explorer()
        elif event.button() == Qt.RightButton:
            # Show context menu
            pass

    def resizeEvent(self, event: QResizeEvent) -> None:
        if self.filepath and event.size().width() != event.oldSize().width():
            self.setText(self.truncate_single_filepath(self.filepath))
        return super().resizeEvent(event)
