# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import override

from PySide6.QtCore import QEvent, Qt, Signal, SignalInstance
from PySide6.QtGui import QAction, QEnterEvent
from PySide6.QtWidgets import QSizePolicy, QWidget

from tagstudio.core.library.alchemy.models import TagColorGroup
from tagstudio.i18n.translations import Translations
from tagstudio.qt.helpers.escape_text import escape_text
from tagstudio.qt.views.capsule_view import CapsuleView
from tagstudio.qt.views.styles.stylesheets import tag_colors


class Capsule(QWidget):
    """A generic tag-like widget used for tags, colors, field templates, etc."""

    on_click = Signal()
    on_edit = Signal()
    on_remove = Signal()
    on_search = Signal()

    def __init__(
        self,
        has_edit: bool = False,
        has_remove: bool = False,
        search_label: str | None = None,
        padded: bool = False,
    ) -> None:
        super().__init__()
        self.has_remove = has_remove

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.setLayout(CapsuleView(padded))

        self.layout().button.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        if has_edit:
            self._add_action(Translations["generic.edit"], self.on_edit)
        if search_label:
            self._add_action(search_label, self.on_search)

        self._connect_callbacks()
        self.set_color_group(None)

    def _connect_callbacks(self) -> None:
        view = self.layout()
        view.button.clicked.connect(self.on_click.emit)
        view.remove_button.clicked.connect(self.on_remove.emit)

    def _add_action(self, text: str, signal: SignalInstance) -> None:
        action = QAction(text, self)
        action.triggered.connect(signal.emit)
        self.layout().button.addAction(action)

    def set_text(self, text: str) -> None:
        self.layout().button.setText(escape_text(text))

    def set_color_group(self, color_group: TagColorGroup | None) -> None:
        """Set the colors from a tag color group, or the default tag colors if `None`."""
        self.layout().set_colors(*tag_colors(color_group))

    @override
    def layout(self) -> CapsuleView:
        return super().layout()  # pyright: ignore[reportReturnType]

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        if self.has_remove:
            self.layout().remove_button.setHidden(False)
        self.update()
        return super().enterEvent(event)

    @override
    def leaveEvent(self, event: QEvent) -> None:
        if self.has_remove:
            self.layout().remove_button.setHidden(True)
        self.update()
        return super().leaveEvent(event)
