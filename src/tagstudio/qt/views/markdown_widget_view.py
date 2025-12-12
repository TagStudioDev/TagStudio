from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver


MARKDOWN_RESOURCE_PATH = Path(Path(__file__).parents[2] / "resources" / "markdown")
FALLBACK_LANGUAGE: str = "en"


class MarkdownWidgetView(QLabel):
    def __init__(self, driver: "QtDriver"):
        super().__init__()
        self.__driver = driver

        self.setTextFormat(Qt.TextFormat.MarkdownText)

    def set_file(self, file_path: Path):
        current_language: str = self.__driver.settings.language

        try:
            with open(Path(MARKDOWN_RESOURCE_PATH / current_language / file_path)) as markdown_file:
                self.setText(markdown_file.read())
        except FileNotFoundError:
            with open(
                Path(MARKDOWN_RESOURCE_PATH / FALLBACK_LANGUAGE / file_path)
            ) as markdown_file:
                self.setText(markdown_file.read())
