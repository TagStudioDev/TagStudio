# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import override

from PySide6.QtCore import QEvent, QObject, QRect, QSize, Qt, Signal, SignalInstance
from PySide6.QtGui import QAction, QColor, QEnterEvent, QMouseEvent, QPainter, QPaintEvent
from PySide6.QtWidgets import QGraphicsOpacityEffect, QSizePolicy, QWidget

from tagstudio.core.library.alchemy.models import TagColorGroup
from tagstudio.i18n.translations import Translations
from tagstudio.qt.helpers.escape_text import escape_text
from tagstudio.qt.views.capsule_view import CapsuleView
from tagstudio.qt.views.styles.stylesheets import RADIUS, TagShape, capsule_colors
from tagstudio.qt.views.styles.tag_icons import icon_shrink, paint_icon
from tagstudio.qt.views.styles.widget_effects import WidgetEffects

_DASHED_LINE_REST_OPACITY = 0.4


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
        is_tag: bool = False,
        is_stretched: bool = False,
        is_dashed: bool = False,
    ) -> None:
        super().__init__()
        self._colors = capsule_colors(None)
        self._effect = WidgetEffects()
        self._icon: bytes | None = None
        self._is_clickable = True
        self._is_colorless = True
        self._is_dashed = is_dashed
        self._is_pill = False
        self._is_stretched = is_stretched
        self._is_tag = is_tag
        self.has_remove = has_remove

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.setLayout(CapsuleView())

        self._fade = QGraphicsOpacityEffect(self)
        self._fade.setOpacity(0.5)
        self._fade.setEnabled(False)
        self.setGraphicsEffect(self._fade)

        self.layout().button.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self._edit_action: QAction | None = None
        if has_edit:
            self._edit_action = self._add_action(Translations["generic.edit"], self.on_edit)
        if search_label:
            self._add_action(search_label, self.on_search)

        self._connect_callbacks()
        self.set_color_group(None)

    def _connect_callbacks(self) -> None:
        view = self.layout()
        view.button.clicked.connect(self._on_button_clicked)
        view.button.installEventFilter(self)
        view.remove_button.clicked.connect(self.on_remove.emit)

    def _add_action(self, text: str, signal: SignalInstance) -> QAction:
        action = QAction(text, self)
        action.triggered.connect(signal.emit)
        self.layout().button.addAction(action)
        return action

    def _on_button_clicked(self) -> None:
        if self._is_clickable:
            self.on_click.emit()

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if (
            not self._is_clickable
            and isinstance(event, QMouseEvent)
            and event.button() == Qt.MouseButton.LeftButton
        ):
            return True
        return super().eventFilter(watched, event)

    def set_clickable(self, clickable: bool) -> None:
        self._is_clickable = clickable
        self._fade.setEnabled(not clickable)
        self.setCursor(
            Qt.CursorShape.PointingHandCursor if clickable else Qt.CursorShape.ArrowCursor
        )

    def set_is_tag(self, is_tag: bool) -> None:
        self._is_tag = is_tag
        self.restyle()

    def set_edit_enabled(self, enabled: bool) -> None:
        if self._edit_action is not None:
            self._edit_action.setEnabled(enabled)

    def set_text(self, text: str) -> None:
        self.layout().button.setText(escape_text(text))

    def set_color_group(self, color_group: TagColorGroup | None) -> None:
        """Set the colors from a tag color group, or the default tag colors if `None`."""
        self._colors = capsule_colors(color_group)
        self._is_colorless = color_group is None
        self.restyle()

    def set_icon(self, icon: bytes | None) -> None:
        """Show an SVG icon left of the text."""
        if icon != self._icon:
            self._icon = icon
            self.restyle()

    def restyle(self) -> None:
        """Style the capsule with its colors, icon, and shape."""
        # NOTE: Only tag capsules follow the pill-shaped tag setting
        self._is_pill = self._is_tag and TagShape.is_pill
        shrink = None
        if self._icon is not None:
            shrink = icon_shrink(self._icon, CapsuleView.HEIGHT, self._radius())
        self.layout().set_colors(
            *self._colors,
            is_pill=self._is_pill,
            icon_shrink=shrink,
            is_stretched=self._is_stretched,
        )
        self.update()

    def _radius(self) -> float:
        return CapsuleView.HEIGHT // 2 if self._is_pill else RADIUS

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        # Paints the body under the button, and the button only draws the text
        primary, border, highlight, text = self._colors
        button = self.layout().button
        rect = button.geometry()
        radius = self._radius()

        painter = QPainter(self)
        is_down = self._is_clickable and button.isDown()
        is_hovered = self._is_clickable and button.underMouse()
        if self._is_dashed:
            fill = highlight if is_down else primary if is_hovered else None
            line = QColor(text)
            line.setAlphaF(1.0 if is_down or is_hovered else _DASHED_LINE_REST_OPACITY)
            self._effect.paint_dashed_capsule(painter, rect, radius, fill, line)
        else:
            self._effect.paint_capsule(
                painter,
                rect,
                radius,
                primary,
                border,
                highlight,
                is_down=is_down,
                is_hovered=is_hovered,
                is_colorless=self._is_colorless,
            )
        view = self.layout()
        if self._icon is not None and view.remove_button.isHidden():
            icon_slot = QRect(rect.topLeft(), QSize(view.HEIGHT, view.HEIGHT))
            icon_color = primary if is_down else text
            paint_icon(painter, icon_slot, radius, self._icon, icon_color)
        if button.hasFocus() and self.window().testAttribute(
            Qt.WidgetAttribute.WA_KeyboardFocusChange
        ):
            self._effect.paint_focus_ring(painter, rect, radius)
        painter.end()

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
