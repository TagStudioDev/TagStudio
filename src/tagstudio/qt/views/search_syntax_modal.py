from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QScrollArea, QVBoxLayout, QWidget

from tagstudio.qt.translations import Translations
from tagstudio.qt.views.markdown_widget_view import MarkdownWidgetView

if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver


class SearchSyntaxModal(QWidget):
    def __init__(self, driver: "QtDriver"):
        super().__init__()

        # Modal
        self.setWindowTitle(Translations["search_syntax.title"])

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(320, 720)
        self.__root_layout = QVBoxLayout(self)
        self.__root_layout.setSpacing(0)
        self.__root_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)

        # Scroll
        self.__scroll_area = QScrollArea()
        self.__scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.__scroll_area.setWidgetResizable(True)
        self.__scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.__scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.__root_layout.addWidget(self.__scroll_area)

        # Content
        self.__content: MarkdownWidgetView = MarkdownWidgetView(driver)
        self.__content.set_file(Path("search_syntax_cheatsheet.md"))
        self.__content.setWordWrap(True)
        self.__scroll_area.setWidget(self.__content)

        # Close button
        self.__buttons_row = QWidget()
        self.__buttons_row_layout = QHBoxLayout(self.__buttons_row)
        self.__buttons_row_layout.setContentsMargins(12, 12, 12, 12)
        self.__buttons_row_layout.addStretch(1)
        self.__root_layout.addWidget(self.__buttons_row)

        self.__close_button = QPushButton(Translations["generic.close"])
        self.__close_button.clicked.connect(lambda: self.close())
        self.__buttons_row_layout.addWidget(self.__close_button)
