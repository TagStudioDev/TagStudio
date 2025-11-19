from pathlib import Path

import structlog
from superqt.utils import CodeSyntaxHighlight

from tagstudio.qt.views.preview_panel.thumbnail.text_display_view import TextDisplayView

logger = structlog.get_logger(__name__)


class TextDisplayController(TextDisplayView):
    def __init__(self) -> None:
        super().__init__()

    def set_file(self, path: Path):
        language: str = path.suffix[1:]

        try:
            with open(path) as text_file:
                content: str = text_file.read()

            CodeSyntaxHighlight(self.document(), language, "github-dark")
            self.setText(content)
        except ValueError:
            logger.warn(f"[TextDisplayController] Couldn't find lexer for `{language}`")
