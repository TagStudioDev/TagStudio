import contextlib
from pathlib import Path
from typing import TYPE_CHECKING

import structlog
from pygments.lexer import Lexer
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound
from superqt.utils import CodeSyntaxHighlight

from tagstudio.qt.views.preview_panel.thumbnail.text_display_view import TextDisplayView

if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class TextDisplayController(TextDisplayView):
    """A widget for displaying a plaintext file."""

    def __init__(self, driver: "QtDriver") -> None:
        super().__init__()
        self.driver = driver

    def set_file(self, path: Path) -> None:
        """Sets the text file that the text display displays.

        Args:
            path (Path): The path of the text file.

        """
        language: str = path.suffix[1:]
        content: str = ""

        try:
            with open(path) as text_file:
                content = text_file.read()

            if lexer_exists(language):
                CodeSyntaxHighlight(
                    self.document(), language, self.driver.settings.syntax_highlighting_style
                )
            else:
                logger.warn(f"[TextDisplayController] Couldn't find lexer for `{language}`")

            self.setText(content)
        except FileNotFoundError:
            logger.error(f"[TextDisplayController] Couldn't find file {path}")


def lexer_exists(language: str) -> bool:
    lexer: Lexer | None = None

    with contextlib.suppress(ClassNotFound):
        lexer = get_lexer_by_name(language)

    return lexer is not None
