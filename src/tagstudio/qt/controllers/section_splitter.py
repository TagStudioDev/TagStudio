# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from functools import partial
from typing import override

from PySide6.QtCore import Qt
from PySide6.QtGui import QPaintEvent
from PySide6.QtWidgets import QSplitter, QSplitterHandle

from tagstudio.qt.controllers.collapsible_section import CollapsibleSection
from tagstudio.qt.controllers.size_animation import SizeAnimation
from tagstudio.qt.views.styles.stylesheets import HALF_PAD, PAD
from tagstudio.qt.views.styles.tagstudio_style import set_handle_span, set_shown_at_rest


class _SectionHandle(QSplitterHandle):
    """A splitter handle with an optional hairline when disabled."""

    def __init__(self, orientation: Qt.Orientation, splitter: QSplitter) -> None:
        super().__init__(orientation, splitter)
        self._is_line_shown = True

    @override
    def paintEvent(self, arg__1: QPaintEvent) -> None:
        if self._is_line_shown:
            super().paintEvent(arg__1)

    def set_state(self, resizable: bool, line_shown: bool) -> None:
        self.setEnabled(resizable)
        self.setCursor(Qt.CursorShape.SplitVCursor if resizable else Qt.CursorShape.ArrowCursor)
        self._is_line_shown = line_shown
        self.update()


class SectionSplitter(QSplitter):
    """A vertical splitter of collapsible sections."""

    def __init__(self, sections: list[CollapsibleSection]) -> None:
        super().__init__(Qt.Orientation.Vertical)
        self.sections = sections
        self.setChildrenCollapsible(False)
        self.setHandleWidth(HALF_PAD * 2)
        set_handle_span(self, PAD)
        set_shown_at_rest(self, shown=False)
        for section in sections:
            self.addWidget(section)
        self.setStretchFactor(0, 1)

        self._animations = [SizeAnimation(section) for section in sections]
        for index, section in enumerate(sections):
            section.collapse_button.clicked.connect(partial(self.toggle_collapsed, index))
            self._animations[index].height_set.connect(section.fit_contents)
            self._animations[index].finished.connect(section.finish_contents)

    @override
    def createHandle(self) -> _SectionHandle:
        return _SectionHandle(self.orientation(), self)

    def toggle_collapsed(self, index: int) -> None:
        section = self.sections[index]
        section.set_collapsed(not section.is_collapsed)
        self._update_handles()
        animation = self._animations[index]
        if section.is_collapsed:
            animation.collapse_to(section.header_height)
        else:
            animation.expand_to(self._expanded_height(section, animation.full_height()))

    def _expanded_height(self, section: CollapsibleSection, remembered_height: int) -> int:
        """The height a section expands to, filling the splitter if it's the only one open."""
        others = [s for s in self.sections if s is not section]
        others_height = sum(
            s.header_height if s.is_collapsed else s.minimumSizeHint().height() for s in others
        )
        handles_height = self.handleWidth() * len(others)
        available_height = self.height() - others_height - handles_height
        if all(s.is_collapsed for s in others):
            return available_height
        return min(remembered_height, available_height)

    def _update_handles(self) -> None:
        """Disable handles beside collapsed sections, hiding any under an open section."""
        for index, section in enumerate(self.sections[1:], start=1):
            above = self.sections[index - 1]
            handle = self.handle(index)
            assert isinstance(handle, _SectionHandle)
            if section.is_collapsed and not above.is_collapsed:
                handle.set_state(resizable=False, line_shown=False)
            elif section.is_collapsed or above.is_collapsed:
                handle.set_state(resizable=False, line_shown=True)
            else:
                handle.set_state(resizable=True, line_shown=True)
