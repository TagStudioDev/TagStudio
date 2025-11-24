from pathlib import Path
from typing import TYPE_CHECKING

import structlog
from superqt.utils import CodeSyntaxHighlight

from tagstudio.qt.views.preview_panel.thumbnail.text_display_view import TextDisplayView

if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class TextDisplayController(TextDisplayView):
    def __init__(self, driver: "QtDriver") -> None:
        super().__init__()
        self.driver = driver

    def set_file(self, path: Path):
        language: str = path.suffix[1:]

        try:
            with open(path) as text_file:
                content: str = text_file.read()

            CodeSyntaxHighlight(
                self.document(), language, self.driver.settings.syntax_highlighting_style
            )
            self.setText(content)
        except ValueError:
            logger.warn(f"[TextDisplayController] Couldn't find lexer for `{language}`")
        except FileNotFoundError:
            logger.error(f"[TextDisplayController] Couldn't find file {path}")
