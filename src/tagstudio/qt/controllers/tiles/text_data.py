# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import re
from typing import override

from tagstudio.qt.controllers.tiles.tile_data import TileData
from tagstudio.qt.views.tiles.text_data_view import TextDataView


class TextData(TileData):
    """An inner widget for any text that goes in a Tile widget.

    Can include text fields, date fields, etc.
    """

    def __init__(self, title: str, text: str) -> None:
        super().__init__(title, TextDataView())
        self.setObjectName("text_data")
        self.set_text(text)

    @override
    def layout(self) -> TextDataView:
        return super().layout()  # pyright: ignore[reportReturnType]

    def set_text(self, text: str):
        text = linkify(text)
        self.layout().text_label.setText(text)


# Regex from https://stackoverflow.com/a/6041965
def linkify(text: str):
    url_pattern = r"(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#\-*]*[\w@?^=%&\/~+#\-*])"  # noqa: E501
    return re.sub(
        url_pattern,
        lambda url: f'<a href="{url.group(0)}">{url.group(0)}</a>',
        text,
        flags=re.IGNORECASE,
    )
