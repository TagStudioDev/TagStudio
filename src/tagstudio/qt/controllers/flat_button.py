# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import override

from PySide6.QtCore import QPointF, QSize, Qt, QVariantAnimation
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QPushButton

from tagstudio.qt.views.styles.color_overlay import svg_color_overlay, theme_foreground_color
from tagstudio.qt.views.styles.palette import Palette
from tagstudio.qt.views.styles.stylesheets import FLAT_ICON_SIZE, MED_HEIGHT, item_thumb_hover_color

_SPIN_DURATION_MS = 2000
_DISABLED_OPACITY = 0.5


class FlatButton(QPushButton):
    """An icon-only button, using outlined/solid variants to indicate its state."""

    def __init__(self, svg: bytes, solid_svg: bytes, icon_size: int = FLAT_ICON_SIZE) -> None:
        super().__init__()
        self._svg = svg
        self._solid_svg = solid_svg
        self._icon_size = icon_size
        self._angle = 0.0
        self._spin = QVariantAnimation(self)
        self._spin.setStartValue(360.0)
        self._spin.setEndValue(0.0)
        self._spin.setDuration(_SPIN_DURATION_MS)
        self._spin.setLoopCount(-1)
        self._spin.valueChanged.connect(self._set_angle)
        self.setFixedSize(MED_HEIGHT, MED_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def set_spinning(self, spinning: bool) -> None:
        """Start or stop spinning the icon."""
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, spinning)
        if spinning:
            self._spin.start()
        else:
            self._spin.stop()
            self._set_angle(0.0)

    def _set_angle(self, angle: float) -> None:
        self._angle = angle
        self.update()

    def _is_spinning(self) -> bool:
        return self.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def _icon_color(self) -> QColor:
        if self._is_spinning() or not self.isEnabled():
            return theme_foreground_color()
        if self.isDown() or self.isChecked():
            return Palette.accent_alt()
        if self.underMouse():
            return item_thumb_hover_color()
        return theme_foreground_color()

    @override
    def paintEvent(self, arg__1: QPaintEvent) -> None:
        svg = self._solid_svg if self.isDown() or self.isChecked() else self._svg
        side = self._icon_size
        pixmap = svg_color_overlay(
            svg, self._icon_color(), self.devicePixelRatioF(), QSize(side, side)
        )
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if self._is_spinning() or not self.isEnabled():
            painter.setOpacity(_DISABLED_OPACITY)
        painter.translate(QPointF(self.rect().center()) + QPointF(0.5, 0.5))
        painter.rotate(self._angle)
        painter.drawPixmap(QPointF(-side / 2, -side / 2), pixmap)
        painter.end()
