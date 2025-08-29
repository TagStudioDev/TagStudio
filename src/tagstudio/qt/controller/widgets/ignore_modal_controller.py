# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from pathlib import Path
from typing import override

import structlog
from PySide6 import QtGui
from PySide6.QtCore import Signal

from tagstudio.core.constants import IGNORE_NAME, TS_FOLDER_NAME
from tagstudio.core.library.alchemy.library import Library, Tag
from tagstudio.core.library.ignore import Ignore
from tagstudio.qt.helpers import file_opener
from tagstudio.qt.view.widgets.ignore_modal_view import IgnoreModalView

logger = structlog.get_logger(__name__)


class IgnoreModal(IgnoreModalView):
    on_edit = Signal(Tag)

    def __init__(self, library: Library) -> None:
        super().__init__(library)
        self.open_button.clicked.connect(self.__open_file)

    def __load_file(self):
        if not self.lib.library_dir:
            return
        ts_ignore: list[str] = Ignore.read_ignore_file(self.lib.library_dir)
        self.text_edit.setPlainText("".join(ts_ignore))

    def __open_file(self):
        if not self.lib.library_dir:
            return
        ts_ignore_path = Path(self.lib.library_dir / TS_FOLDER_NAME / IGNORE_NAME)
        file_opener.open_file(ts_ignore_path, file_manager=True)

    def save(self):
        if not self.lib.library_dir:
            return
        lines = self.text_edit.toPlainText().split("\n")
        lines = [f"{line}\n" for line in lines]
        Ignore.write_ignore_file(self.lib.library_dir, lines)

    @override
    def showEvent(self, event: QtGui.QShowEvent) -> None:  # type: ignore
        self.__load_file()
        return super().showEvent(event)
