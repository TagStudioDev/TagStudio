# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from tagstudio.qt.views.inset_scroll_box_view import InsetScrollBoxView
from tagstudio.qt.views.styles.stylesheets import PAD


class InsetScrollBox(QWidget):
    """A scroll area inside an inset frame."""

    def __init__(self) -> None:
        super().__init__()
        self.setLayout(InsetScrollBoxView())
        scroll_bar = self.layout().scroll_area.verticalScrollBar()
        scroll_bar.rangeChanged.connect(self._toggle_scroll_bar)
        self._toggle_scroll_bar(scroll_bar.minimum(), scroll_bar.maximum())

    @override
    def layout(self) -> InsetScrollBoxView:
        layout = super().layout()
        assert isinstance(layout, InsetScrollBoxView)
        return layout

    def set_content_inset(self, inset: int) -> None:
        """Inset the box's content from its left edge."""
        frame_layout = self.layout().frame_layout
        margins = frame_layout.contentsMargins()
        margins.setLeft(inset)
        frame_layout.setContentsMargins(margins)

    def _toggle_scroll_bar(self, minimum: int, maximum: int) -> None:
        """Show the scroll bar only while the content overflows."""
        view = self.layout()
        is_overflowing = maximum > minimum
        margins = view.frame_layout.contentsMargins()
        margins.setRight(0 if is_overflowing else PAD)
        view.frame_layout.setContentsMargins(margins)
        view.frame_layout.activate()
        view.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
            if is_overflowing
            else Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
