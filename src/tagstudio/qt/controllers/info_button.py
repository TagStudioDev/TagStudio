# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import override

from PySide6.QtCore import QEvent, QObject, QPoint, QRect, Qt, QVariantAnimation
from PySide6.QtGui import (
    QColor,
    QEnterEvent,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPixmap,
)
from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QLayout,
)

from tagstudio.core.utils.types import unwrap
from tagstudio.i18n.translations import Translations
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.styles.color_overlay import svg_to_pixmap, theme_foreground_color
from tagstudio.qt.views.styles.palette import ColorType, UiColor, get_ui_color
from tagstudio.qt.views.styles.stylesheets import info_popover_style


class _FadingPopoverEffect(QGraphicsDropShadowEffect):
    """Effect to fade the entire popover, including the drop shadow."""

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        self.opacity: float = 0.0

    @override
    def draw(self, painter: QPainter) -> None:
        painter.setOpacity(self.opacity)
        super().draw(painter)


class InfoButton(QAbstractButton):
    """An ⓘ info button that displays a popover with extra explanations and/or examples."""

    _BUTTON_GAP = 6
    _BUTTON_SIZE = (22, 22)
    _FADE_DURATION = 100
    _SHADOW_ALPHA = 160
    _WINDOW_MARGIN = 12

    def __init__(self, content: QLayout, title: str, popover_width: int = 360) -> None:
        super().__init__()
        self.setToolTip(Translations.format("info.tooltip.about", title=title))
        self.setAccessibleName(self.toolTip())
        self.setFixedSize(*self._BUTTON_SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._popover = QFrame(self)
        self._popover.setObjectName("info_popover")
        self._popover.setFixedWidth(popover_width)
        self._popover.setStyleSheet(info_popover_style())
        self._popover.setLayout(content)
        self._popover.hide()

        self._fade_effect = _FadingPopoverEffect(self._popover)
        self._fade_effect.setBlurRadius(48)
        self._fade_effect.setOffset(0, 3)
        self._fade_effect.setColor(QColor(0, 0, 0, self._SHADOW_ALPHA))
        self._popover.setGraphicsEffect(self._fade_effect)

        self._is_open = False
        self._update_icon(hovered=False)
        self._fade = QVariantAnimation(self)
        self._fade.setDuration(self._FADE_DURATION)
        self._fade.valueChanged.connect(self._set_opacity)
        self._fade.finished.connect(self._on_fade_finished)

        self.clicked.connect(self._toggle_popover)

    def _toggle_popover(self) -> None:
        if self._is_open:
            self._hide_popover()
            return

        # Overlay the popover inside the current window, below the button.
        # If there's no room below, flip it above.
        window = self.window()
        if self._popover.parent() is not window:
            self._popover.setParent(window)
        width = self._popover.width()
        height = self._popover.heightForWidth(width)
        self._popover.resize(width, height)
        pos = self.mapTo(window, QPoint(self.width() - width, self.height() + self._BUTTON_GAP))
        if pos.y() + height > window.height() - self._WINDOW_MARGIN:
            pos.setY(self.mapTo(window, QPoint(0, 0)).y() - height - self._BUTTON_GAP)
        pos.setX(
            max(self._WINDOW_MARGIN, min(pos.x(), window.width() - width - self._WINDOW_MARGIN))
        )
        pos.setY(max(self._WINDOW_MARGIN, pos.y()))

        self._popover.move(pos)
        self._popover.raise_()
        self._popover.show()
        self._is_open = True
        self._update_icon(self.underMouse())
        self._fade_to(1.0)
        unwrap(QApplication.instance()).installEventFilter(self)

    def _hide_popover(self) -> None:
        self._is_open = False
        self._update_icon(self.underMouse())
        self._fade_to(0.0)
        unwrap(QApplication.instance()).removeEventFilter(self)

    def _fade_to(self, opacity: float) -> None:
        self._fade.stop()
        self._fade.setStartValue(self._fade_effect.opacity)
        self._fade.setEndValue(opacity)
        self._fade.start()

    def _set_opacity(self, opacity: float) -> None:
        self._fade_effect.opacity = opacity
        # This cubes the opacity to use for the shadow alpha so it's faint until near the end.
        self._fade_effect.setColor(QColor(0, 0, 0, round(self._SHADOW_ALPHA * opacity**3)))
        self._fade_effect.update()

    def _on_fade_finished(self) -> None:
        if not self._is_open:
            self._popover.hide()

    def _update_icon(self, hovered: bool) -> None:
        rm = ResourceManager()
        svg = rm.info_solid if self._is_open else rm.info_outline
        color = (
            QColor.fromString(get_ui_color(ColorType.PRIMARY, UiColor.BLUE))
            if hovered
            else theme_foreground_color()
        )
        self._icon: QPixmap = svg_to_pixmap(svg, color, self.devicePixelRatioF(), self.size())
        self.update()

    @override
    def paintEvent(self, e: QPaintEvent) -> None:
        QPainter(self).drawPixmap(0, 0, self._icon)

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        self._update_icon(hovered=True)
        super().enterEvent(event)

    @override
    def leaveEvent(self, event: QEvent) -> None:
        self._update_icon(hovered=False)
        super().leaveEvent(event)

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if isinstance(event, QMouseEvent) and event.type() == QEvent.Type.MouseButtonPress:
            click_pos = event.globalPosition().toPoint()
            button_rect = QRect(self.mapToGlobal(QPoint(0, 0)), self.size())
            popover_rect = QRect(self._popover.mapToGlobal(QPoint(0, 0)), self._popover.size())
            # Clicks outside the popover or the ⓘ button will close it
            if not button_rect.contains(click_pos) and not popover_rect.contains(click_pos):
                self._hide_popover()
        elif (
            isinstance(event, QKeyEvent)
            and event.type() == QEvent.Type.KeyPress
            and event.key() == Qt.Key.Key_Escape
        ):
            self._hide_popover()
            return True
        elif event.type() == QEvent.Type.Resize and watched is self.window():
            self._hide_popover()
        return super().eventFilter(watched, event)
