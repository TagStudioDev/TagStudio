# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import math
from typing import override

from PySide6.QtCore import QPoint, QRect, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPainterPath, QPaintEvent
from PySide6.QtWidgets import QCheckBox, QWidget

from tagstudio.core.library.alchemy.models import Tag, TagColorGroup
from tagstudio.qt.views.capsule_view import CapsuleView
from tagstudio.qt.views.styles.palette import shade
from tagstudio.qt.views.styles.stylesheets import (
    RADIUS,
    TagShape,
    capsule_colors,
    get_tinted_tag_text_color,
    is_dark_theme,
)
from tagstudio.qt.views.styles.tag_icons import paint_icon
from tagstudio.qt.views.styles.widget_effects import (
    IMAGE_EXTRA_HIGHLIGHT_LIGHT,
    IMAGE_HIGHLIGHT,
    IMAGE_SCREEN,
    IMAGE_SHADOW_BURN,
    IMAGE_SHADOW_DARK,
    IMAGE_SHADOW_LIGHT,
    WidgetEffects,
)

_UNCHECKED_ICON_OPACITY = 0.5
_HOVERED_ICON_OPACITY = 1
_BORDER_COLOR_WIDTH = 1
_BODY_DARKNESS = 0.8
_BODY_BURN = 0.5
_BODY_OPACITY = 0.8


def _body_color(color: QColor) -> QColor:
    """An unchecked badge's body color."""
    opaque = QColor(color)
    opaque.setAlpha(255)
    return shade(opaque, _BODY_DARKNESS, _BODY_BURN)


class Badge(QCheckBox):
    """A checkbox showing whether an item has a tag, drawn in the tag's colors.

    Args:
        icon (bytes): The SVG icon.
        is_circular (bool | None): Whether the shape is circular or square.
            `None` will use the app's setting's value.
        unchecked_icon (bytes | None): An optional different SVG icon to show while unchecked.
    """

    SIZE = CapsuleView.HEIGHT

    def __init__(
        self, icon: bytes, is_circular: bool | None = None, unchecked_icon: bytes | None = None
    ) -> None:
        super().__init__()
        self._underlay_widget: QWidget | None = None
        self._underlay_brush: QBrush | None = None
        self._color_group: TagColorGroup | None = None
        self._effect = WidgetEffects()
        self._icon = icon
        self._is_circular = is_circular
        self._unchecked_icon = unchecked_icon
        self.setFixedSize(self.SIZE, self.SIZE)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)

    def set_tag(self, tag: Tag | None) -> None:
        """Show a tag's color and name."""
        self.setToolTip(tag.name if tag else "")
        self.set_color_group(tag.color if tag else None)

    def set_color_group(self, color_group: TagColorGroup | None) -> None:
        self._color_group = color_group
        self.update()

    def set_underlay(self, brush: QBrush | None, underlay_widget: QWidget) -> None:
        """Set what the badge is drawn on top of."""
        self._underlay_brush = brush
        self._underlay_widget = underlay_widget
        self.update()

    @override
    def hitButton(self, pos: QPoint) -> bool:
        return self.rect().contains(pos)

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        primary, border, highlight, text = capsule_colors(self._color_group)
        radius = self._radius()
        icon = self._icon
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.isChecked():
            self._effect.paint_capsule(
                painter,
                self.rect(),
                radius,
                primary,
                border,
                highlight,
                is_down=self.isDown(),
                is_hovered=self.underMouse(),
                is_colorless=self._color_group is None,
                border_width=_BORDER_COLOR_WIDTH,
            )
            icon_color = text
        else:
            self._paint_unchecked_body(painter, primary)
            if self.isDown():
                icon_color = highlight
            elif self._color_group is None:
                icon_color = get_tinted_tag_text_color(_body_color(primary))
            elif self._color_group.secondary:
                icon_color = QColor(self._color_group.secondary)
            else:
                icon_color = primary
            painter.setOpacity(
                _HOVERED_ICON_OPACITY if self.underMouse() else _UNCHECKED_ICON_OPACITY
            )
            if self._unchecked_icon is not None:
                icon = self._unchecked_icon

        paint_icon(painter, self.rect(), radius, icon, icon_color)
        if self.hasFocus() and self.window().testAttribute(
            Qt.WidgetAttribute.WA_KeyboardFocusChange
        ):
            painter.setOpacity(1)
            self._effect.paint_focus_ring(painter, self.rect(), radius)
        painter.end()

    def _paint_unchecked_body(self, painter: QPainter, color: QColor) -> None:
        """Paint an unchecked badge's body."""
        body = _body_color(color)
        radius = self._radius()
        if self._underlay_widget is None:
            self._effect.paint_debossed(painter, self.rect(), radius, body)
            return

        is_dark = is_dark_theme()
        shadow_color = IMAGE_SHADOW_DARK if is_dark else IMAGE_SHADOW_LIGHT
        shadow = shade(body, shadow_color.alphaF(), IMAGE_SHADOW_BURN)
        pixel_ratio = self.devicePixelRatioF()
        side = math.ceil(self.SIZE * pixel_ratio)
        layer = QImage(side, side, QImage.Format.Format_ARGB32_Premultiplied)
        layer.setDevicePixelRatio(pixel_ratio)
        layer.fill(Qt.GlobalColor.transparent)
        layer_painter = QPainter(layer)
        layer_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for inset, brush in ((0, self._rim_brush(is_dark)), (1, QBrush(shadow)), (2, QBrush(body))):
            path = QPainterPath()
            rect = QRectF(self.rect()).adjusted(inset, inset, -inset, -inset)
            path.addRoundedRect(rect, radius - inset, radius - inset)
            layer_painter.fillPath(path, brush)
        layer_painter.end()
        # Fade as one layer
        painter.save()
        painter.setOpacity(_BODY_OPACITY)
        painter.drawImage(QPoint(0, 0), layer)
        painter.restore()

    def _radius(self) -> float:
        is_round = TagShape.is_circle_badge if self._is_circular is None else self._is_circular
        return self.SIZE / 2 if is_round else RADIUS

    def _rim_brush(self, is_dark: bool) -> QBrush:
        """The underlay with the image outline's highlight applied."""
        pixel_ratio = self.devicePixelRatioF()
        side = math.ceil(self.SIZE * pixel_ratio)
        layer = QImage(side, side, QImage.Format.Format_ARGB32_Premultiplied)
        layer.setDevicePixelRatio(pixel_ratio)
        layer.fill(Qt.GlobalColor.transparent)
        painter = QPainter(layer)
        if self._underlay_brush is not None and self._underlay_widget is not None:
            # NOTE: Qt drops a brush transform's translation on high DPI pixmaps
            offset = self.mapTo(self._underlay_widget, QPoint(0, 0))
            area = QRect(offset, self.size())
            painter.translate(-offset.x(), -offset.y())
            painter.fillRect(area, self._underlay_brush)
            painter.fillRect(area, IMAGE_HIGHLIGHT)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Screen)
            painter.setOpacity(IMAGE_SCREEN)
            painter.fillRect(area, self._underlay_brush)
            painter.resetTransform()
            painter.setOpacity(1)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        else:
            painter.fillRect(self.rect(), IMAGE_HIGHLIGHT)
        if not is_dark:
            painter.fillRect(self.rect(), IMAGE_EXTRA_HIGHLIGHT_LIGHT)
        painter.end()
        return QBrush(layer)
