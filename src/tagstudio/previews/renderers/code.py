# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from pathlib import Path
from typing import override

import structlog
from PIL.Image import (
    Image,
)
from pygments.style import Style
from pygments.token import (
    Comment,
    Error,
    Generic,
    Keyword,
    Literal,
    Name,
    Number,
    Operator,
    Other,
    Punctuation,
    String,
    Text,
    Whitespace,
)

from tagstudio.core.enums import Theme
from tagstudio.previews.base_preview import BasePreview
from tagstudio.previews.renderers.text import text_thumb

logger = structlog.get_logger(__name__)


class CodeStyle(Style):
    background = "#111111"
    foreground = "#f8f8f2"
    selection = "#44475a"
    comment = "#6272a4"
    cyan = "#8be9fd"
    green = "#50fa7b"
    orange = "#ffb86c"
    pink = "#ff79c6"
    purple = "#bd93f9"
    red = "#ff5555"
    yellow = "#f1fa8c"
    deletion = "#8b080b"

    background_color = background
    highlight_color = selection
    line_number_color = yellow
    line_number_background_color = selection
    line_number_special_color = green
    line_number_special_background_color = comment

    styles = {
        Whitespace: foreground,
        Comment: comment,
        Comment.Preproc: pink,
        Generic: foreground,
        Generic.Deleted: deletion,
        Generic.Emph: "underline",
        Generic.Heading: "bold",
        Generic.Inserted: "bold",
        Generic.Output: selection,
        Generic.EmphStrong: "underline",
        Generic.Subheading: "bold",
        Error: foreground,
        Keyword: pink,
        Keyword.Constant: pink,
        Keyword.Declaration: cyan + " italic",
        Keyword.Type: cyan,
        Literal: foreground,
        Name: foreground,
        Name.Attribute: green,
        Name.Builtin: cyan + " italic",
        Name.Builtin.Pseudo: foreground,
        Name.Class: green,
        Name.Function: green,
        Name.Label: cyan + " italic",
        Name.Tag: pink,
        Name.Variable: cyan + " italic",
        Number: orange,
        Operator: pink,
        Other: foreground,
        Punctuation: foreground,
        String: purple,
        Text: foreground,
    }


class CodePreview(BasePreview):
    media_type_name = "code"

    @override
    @classmethod
    def render(
        cls,
        filepath: Path,
        theme: Theme,
        size: tuple[int, int],
        dpi_scale: float,
    ) -> Image | None:
        return text_thumb(filepath, size, CodeStyle)
