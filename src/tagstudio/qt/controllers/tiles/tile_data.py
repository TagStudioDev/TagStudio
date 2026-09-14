# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtWidgets import QLayout, QWidget


class TileData(QWidget):
    """A base class for widgets that go in a Tile widget."""

    def __init__(self, title: str, view: QLayout) -> None:
        super().__init__()
        self.title: str = title
        self.setLayout(view)
