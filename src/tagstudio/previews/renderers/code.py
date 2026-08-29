# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from pathlib import Path
from typing import override

import structlog
from PIL.Image import Image
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
from tagstudio.core.media_types import MediaTypes
from tagstudio.previews.base_preview import RENDER, BasePreview
from tagstudio.previews.renderers.text import text_thumb

logger = structlog.get_logger(__name__)

# TODO: Use different syntax highlighting for different filetypes.
# NOTE: Filetype equivalents (i.e. ".ini" == ".inf") are already declared internally.

# CSS
MediaTypes.register("code", ".css", RENDER)
MediaTypes.register("code", ".less", RENDER)
MediaTypes.register("code", ".qss", RENDER)
MediaTypes.register("code", ".sass", RENDER)
MediaTypes.register("code", ".scss", RENDER)
MediaTypes.register("code", ".styl", RENDER)

# HTML
MediaTypes.register("code", ".html", RENDER)

# JavaScript
MediaTypes.register("code", ".cjs", RENDER)
MediaTypes.register("code", ".js", RENDER)
MediaTypes.register("code", ".jsx", RENDER)
MediaTypes.register("code", ".mjs", RENDER)

# TOML
MediaTypes.register("code", ".ini", RENDER)
MediaTypes.register("code", ".toml", RENDER)

# TypeScript
MediaTypes.register("code", ".cts", RENDER)
MediaTypes.register("code", ".ts", RENDER)
MediaTypes.register("code", ".mts", RENDER)
MediaTypes.register("code", ".tsx", RENDER)

# XML
MediaTypes.register("code", ".xml", RENDER)

# YAML
MediaTypes.register("code", [".yaml", ".yml"], RENDER)

# Misc
MediaTypes.register("code", ".cfg", RENDER)
MediaTypes.register("code", ".conf", RENDER)
MediaTypes.register("code", ".config", RENDER)
MediaTypes.register("code", ".lock", RENDER)
MediaTypes.register("code", ".log", RENDER)
MediaTypes.register("code", ".plist", RENDER)
MediaTypes.register("code", ".theme", RENDER)
MediaTypes.register("code", ".pkginfo", RENDER)


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
    priority = 60

    @override
    @classmethod
    def render(
        cls,
        filepath: Path,
        is_small: bool,
        theme: Theme,
        size: tuple[int, int],
        dpi_scale: float,
    ) -> Image | None:
        return text_thumb(filepath, size, CodeStyle)
