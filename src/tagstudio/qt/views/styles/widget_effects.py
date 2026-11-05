# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


import colorsys
import math
from enum import Enum, auto

from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPalette,
    QPen,
    QRegion,
)
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget

from tagstudio.qt.views.styles.palette import (
    ColorType,
    Palette,
    UiColor,
    blend,
    get_ui_color,
    shade,
)
from tagstudio.qt.views.styles.stylesheets import INNER_RADIUS, RADIUS, is_dark_theme

# Embossed Surfaces
_DASHED_CAPSULE_LINE_WIDTH = 2
_DASHED_CAPSULE_PATTERN = [3, 2]
_EMBOSSED_GRADIENT_FULL_HEIGHT = 24
_EMBOSSED_FILL_ALPHA_DARK = 15
_EMBOSSED_FILL_ALPHA_LIGHT = 170
_EMBOSSED_FILL_ALPHA_HOVER_LIGHT = 255
_EMBOSSED_GRADIENT_TOP_ALPHA = 10
_EMBOSSED_GRADIENT_TOP_ALPHA_HOVER = 20
_EMBOSSED_GRADIENT_TOP_ALPHA_DOWN = 5
_EMBOSSED_GRADIENT_BOTTOM_ALPHA_DARK = 50
_EMBOSSED_GRADIENT_BOTTOM_ALPHA_LIGHT = 16
_EMBOSSED_INNER_OUTLINE_ALPHAS_DARK = (32, 20)  # (Top, Bottom)
_EMBOSSED_INNER_OUTLINE_ALPHAS_LIGHT = (255, 255)
_EMBOSSED_OUTER_OUTLINE_ALPHAS_DARK = (127, 255)
_EMBOSSED_OUTER_OUTLINE_ALPHAS_LIGHT = (48, 80)
_EMBOSSED_OUTER_OUTLINE_ALPHAS_HOVER_LIGHT = (80, 128)

# Debossed Surfaces
DEBOSSED_OUTLINE_WIDTH = 2  # A debossed surface's inner and outer outlines combined
_DEBOSSED_GRADIENT_FULL_HEIGHT = 300
_DEBOSSED_SOLID_MAX_HEIGHT = 24
_DEBOSSED_GRADIENT_ALPHAS_DARK = (90, 120)  # (Top, Bottom)
_DEBOSSED_GRADIENT_ALPHAS_LIGHT = (18, 24)
_DEBOSSED_INNER_OUTLINE_ALPHAS_DARK = (80, 255)
_DEBOSSED_INNER_OUTLINE_ALPHAS_LIGHT = (30, 60)
_DEBOSSED_OUTER_OUTLINE_ALPHAS_DARK = (15, 28)
_DEBOSSED_OUTER_OUTLINE_ALPHAS_LIGHT = (255, 255)

# Colored Tags/Capsules
_CAPSULE_SHADOW_DARKNESS_MIN = 0.3  # For darker colors, up to black
_CAPSULE_SHADOW_DARKNESS_MAX = 0.5  # For lighter colors, up to white
_CAPSULE_SHADOW_DARKNESS_SCALE_LIGHT = 0.75
_CAPSULE_SHADOW_BURN = 0.4
_CAPSULE_HIGHLIGHT_TOP = QColor(255, 255, 255, 255)
_CAPSULE_HIGHLIGHT_BOTTOM = QColor(255, 255, 255, 127)
_CAPSULE_HIGHLIGHT_OPACITY_MIN = 0.4  # For darker colors, up to black
_CAPSULE_HIGHLIGHT_OPACITY_MAX = 1.0  # For lighter colors, up to white
_CAPSULE_EXTRA_HIGHLIGHT_OPACITY_LIGHT = 0.15
_CAPSULE_EXTRA_HIGHLIGHT_OPACITY_DARK = 0.35
_CAPSULE_EXTRA_HIGHLIGHT_THRESHOLD_DARK = 0.55  # Color's lightness needed for extra highlight

# Colorless Tags/Capsules
_COLORLESS_SHADOW_DARKNESS_DARK = 0.75
_COLORLESS_SHADOW_DARKNESS_LIGHT = 0.4
_COLORLESS_HIGHLIGHT_TOP_DARK = QColor(255, 255, 255, 180)
_COLORLESS_HIGHLIGHT_BOTTOM_DARK = QColor(255, 255, 255, 48)
_COLORLESS_HIGHLIGHT_TOP_LIGHT = QColor(255, 255, 255, 255)
_COLORLESS_HIGHLIGHT_BOTTOM_LIGHT = QColor(255, 255, 255, 120)

# Image Outlines (Tuned for contrast on random colors and patterns)
IMAGE_HIGHLIGHT = QColor(255, 255, 255, 25)
IMAGE_EXTRA_HIGHLIGHT_LIGHT = QColor(255, 255, 255, 38)
IMAGE_SCREEN = 0.15
IMAGE_SHADOW_DARK = QColor(0, 0, 0, 179)
IMAGE_SHADOW_LIGHT = QColor(0, 0, 0, 45)
IMAGE_SHADOW_BURN = 0.5


class SurfaceStyle(Enum):
    DEBOSSED = auto()
    EMBOSSED = auto()


def fill_path(rect: QRect, radius: float) -> QPainterPath:
    """A rect's fill, rounded with `radius`."""
    path = QPainterPath()
    # Inset to the outer outline's inner edge so the translucent fill and outline don't overlap
    path.addRoundedRect(QRectF(rect).adjusted(1, 1, -1, -1), radius - 0.5, radius - 0.5)
    return path


def rounded_rect_path(
    rect: QRectF, radius: float, square_edges: Qt.Edge | None = None
) -> QPainterPath:
    """A rounded rect's path. Squared edges are used in special cases, like connected widgets."""
    path = QPainterPath()
    if not square_edges:
        path.addRoundedRect(rect, radius, radius)
        return path

    def corner_radius(*edges: Qt.Edge) -> float:
        return 0 if any(square_edges & edge for edge in edges) else radius

    top_left = corner_radius(Qt.Edge.LeftEdge, Qt.Edge.TopEdge)
    top_right = corner_radius(Qt.Edge.RightEdge, Qt.Edge.TopEdge)
    bottom_right = corner_radius(Qt.Edge.RightEdge, Qt.Edge.BottomEdge)
    bottom_left = corner_radius(Qt.Edge.LeftEdge, Qt.Edge.BottomEdge)
    path.moveTo(rect.left() + top_left, rect.top())
    path.lineTo(rect.right() - top_right, rect.top())
    if top_right:
        diameter = top_right * 2
        path.arcTo(QRectF(rect.right() - diameter, rect.top(), diameter, diameter), 90, -90)
    path.lineTo(rect.right(), rect.bottom() - bottom_right)
    if bottom_right:
        diameter = bottom_right * 2
        path.arcTo(
            QRectF(rect.right() - diameter, rect.bottom() - diameter, diameter, diameter), 0, -90
        )
    path.lineTo(rect.left() + bottom_left, rect.bottom())
    if bottom_left:
        diameter = bottom_left * 2
        path.arcTo(QRectF(rect.left(), rect.bottom() - diameter, diameter, diameter), 270, -90)
    path.lineTo(rect.left(), rect.top() + top_left)
    if top_left:
        diameter = top_left * 2
        path.arcTo(QRectF(rect.left(), rect.top(), diameter, diameter), 180, -90)
    path.closeSubpath()
    return path


def _capsule_shadow_color(shadow_source_color: QColor, is_colorless: bool) -> QColor:
    """The shadow outline color for a capsule."""
    # Light theme gets lighter shadows for less contrast
    if is_colorless:
        darkness = (
            _COLORLESS_SHADOW_DARKNESS_DARK if is_dark_theme() else _COLORLESS_SHADOW_DARKNESS_LIGHT
        )
    else:
        # Darken the shadow the lighter the colored capsule is
        min_darkness, max_darkness = _CAPSULE_SHADOW_DARKNESS_MIN, _CAPSULE_SHADOW_DARKNESS_MAX
        darkness = min_darkness + (max_darkness - min_darkness) * _perceived_lightness(
            shadow_source_color
        )
        if not is_dark_theme():
            darkness *= _CAPSULE_SHADOW_DARKNESS_SCALE_LIGHT
    return shade(shadow_source_color, darkness, _CAPSULE_SHADOW_BURN)


def boxed_text_background_color() -> QColor:
    """The background color for boxed text labels, like in the About screen.

    Derived from the debossed colors, and separate from file extension labels.
    """
    top_alpha, bottom_alpha = (
        _DEBOSSED_GRADIENT_ALPHAS_DARK if is_dark_theme() else _DEBOSSED_GRADIENT_ALPHAS_LIGHT
    )
    return QColor(0, 0, 0, round((top_alpha + bottom_alpha) / 2))


def widget_drop_shadow(widget: QWidget) -> None:
    """Give a widget a drop shadow effect."""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(18)
    shadow.setOffset(0, 1)
    shadow.setColor(QColor(0, 0, 0, 100))
    widget.setGraphicsEffect(shadow)


def _embossed_fill(is_down: bool, under_mouse: bool) -> QColor:
    """An embossed surface's fill color."""
    is_dark = is_dark_theme()
    alpha = _EMBOSSED_FILL_ALPHA_DARK if is_dark else _EMBOSSED_FILL_ALPHA_LIGHT
    if is_down:
        alpha //= 2
    elif under_mouse and not is_dark:
        alpha = _EMBOSSED_FILL_ALPHA_HOVER_LIGHT
    return QColor(255, 255, 255, alpha)


def _gradient_strength(height: float, style: SurfaceStyle) -> float:
    """How strong a gradient appears given a rect's `height`, from 0 (flat) to 1 (full gradient)."""
    # Smaller embossed surfaces get less intense gradients
    if style == SurfaceStyle.EMBOSSED:
        return min(height / _EMBOSSED_GRADIENT_FULL_HEIGHT, 1.0)

    # Debossed surfaces at or under a certain height appear solid
    if height <= _DEBOSSED_SOLID_MAX_HEIGHT:
        return 0.0
    return min(height / _DEBOSSED_GRADIENT_FULL_HEIGHT, 1.0)


def _image_shadow_brush(
    image_brush: QBrush, width: int, height: int, radius: int, pixel_ratio: float, color: QColor
) -> QBrush:
    """Return an image brush that's a darkened and color-burned version of an image.

    The "color burn" effect tints the shadow with more of the image's original colors.
    NOTE: The center of the image is skipped, as this brush is intended to be used as an outline.
    """
    layer = QImage(
        math.ceil(width * pixel_ratio),
        math.ceil(height * pixel_ratio),
        QImage.Format.Format_ARGB32_Premultiplied,
    )
    layer.setDevicePixelRatio(pixel_ratio)
    layer.fill(Qt.GlobalColor.transparent)
    rect = QRectF(0, 0, width, height)
    painter = QPainter(layer)
    # Skip the center since this will be used as an outline effect
    center_region = QRegion(QRect(radius, 2, width - radius * 2, height - 4))
    center_region += QRegion(QRect(2, radius, width - 4, height - radius * 2))
    painter.setClipRegion(QRegion(0, 0, width, height) - center_region)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    painter.fillRect(rect, image_brush)
    painter.fillRect(rect, color)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_ColorBurn)
    painter.setOpacity(IMAGE_SHADOW_BURN)
    painter.fillRect(rect, image_brush)
    painter.end()
    return QBrush(layer)


def _outline_path(rect: QRectF, radius: float, width: float) -> QPainterPath:
    """A rounded rect's outline of `width`, inside `rect`."""
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    inner = rect.adjusted(width, width, -width, -width)
    path.addRoundedRect(inner, radius - width, radius - width)
    return path


def _perceived_lightness(color: QColor) -> float:
    """How light a `color` looks (luma) from 0 to 1."""
    return colorsys.rgb_to_yiq(color.redF(), color.greenF(), color.blueF())[0]


def _set_stops(gradient: QLinearGradient, top: QColor, bottom: QColor, strength: float) -> None:
    """Set a gradient's end colors, pulled toward their midpoint as strength drops."""
    towards_middle = (1 - strength) / 2
    gradient.setColorAt(0.0, blend(top, bottom, towards_middle))
    gradient.setColorAt(1.0, blend(bottom, top, towards_middle))


class WidgetEffects:
    def paint_surface(
        self,
        painter: QPainter,
        rect: QRect,
        radius: float = INNER_RADIUS,
        is_down: bool = False,
        under_mouse: bool = False,
        style: SurfaceStyle = SurfaceStyle.EMBOSSED,
    ) -> None:

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        strength = _gradient_strength(rect.height(), style)
        self._paint_background(painter, rect, radius, is_down, under_mouse, style, strength)
        self.paint_outlines(painter, rect, radius, is_down, under_mouse, style)

    def paint_outlines(
        self,
        painter: QPainter,
        rect: QRect,
        radius: float = INNER_RADIUS,
        is_down: bool = False,
        under_mouse: bool = False,
        style: SurfaceStyle = SurfaceStyle.EMBOSSED,
    ) -> None:
        """Paint a surface's inner and outer outlines.

        Used with widgets that paint their own backgrounds.
        """
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rectf = QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5)
        strength = _gradient_strength(rect.height(), style)
        self._paint_outer_outline(painter, rectf, radius, is_down, under_mouse, style, strength)
        self._paint_inner_outline(painter, rectf, radius, is_down, style, strength)

    def paint_debossed(self, painter: QPainter, rect: QRect, radius: float, color: QColor) -> None:
        """Paint a colored debossed surface."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillPath(fill_path(rect, radius), color)
        self.paint_outlines(painter, rect, radius, style=SurfaceStyle.DEBOSSED)

    def paint_window_background(
        self, painter: QPainter, path: QPainterPath, window: QWidget, opacity: float
    ) -> None:
        """Fill a path with the window's background color.

        Keeps tinted window colors, like on macOS.
        """
        painter.save()
        # Erase what's beneath first so macOS shows the window's tint through the fill
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOut)
        painter.fillPath(path, QColor(0, 0, 0, round(255 * opacity)))
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        background = window.palette().color(QPalette.ColorRole.Window)
        background.setAlphaF(background.alphaF() * opacity)
        painter.fillPath(path, background)
        painter.restore()

    def _paint_background(
        self,
        painter: QPainter,
        rect: QRect,
        radius: float,
        is_down: bool,
        under_mouse: bool,
        style: SurfaceStyle = SurfaceStyle.EMBOSSED,
        strength: float = 1.0,
    ) -> None:
        """Fill the rect with a translucent top-to-bottom gradient."""
        painter.setPen(Qt.PenStyle.NoPen)
        path = fill_path(rect, radius)
        rectf = QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5)

        if style == SurfaceStyle.EMBOSSED:
            if is_down:
                top_alpha = _EMBOSSED_GRADIENT_TOP_ALPHA_DOWN
            elif under_mouse:
                top_alpha = _EMBOSSED_GRADIENT_TOP_ALPHA_HOVER
            else:
                top_alpha = _EMBOSSED_GRADIENT_TOP_ALPHA

            painter.setBrush(_embossed_fill(is_down, under_mouse))
            painter.drawPath(path)
            gradient = QLinearGradient(
                rectf.topLeft() if not is_down else rectf.bottomLeft(),
                rectf.bottomLeft() if not is_down else rectf.topLeft(),
            )
            bottom_alpha = (
                _EMBOSSED_GRADIENT_BOTTOM_ALPHA_DARK
                if is_dark_theme()
                else _EMBOSSED_GRADIENT_BOTTOM_ALPHA_LIGHT
            )
            _set_stops(
                gradient, QColor(255, 255, 255, top_alpha), QColor(0, 0, 0, bottom_alpha), strength
            )
            painter.setBrush(gradient)

        elif style == SurfaceStyle.DEBOSSED:
            gradient = QLinearGradient(rectf.topLeft(), rectf.bottomLeft())
            top_alpha, bottom_alpha = (
                _DEBOSSED_GRADIENT_ALPHAS_DARK
                if is_dark_theme()
                else _DEBOSSED_GRADIENT_ALPHAS_LIGHT
            )
            _set_stops(
                gradient, QColor(0, 0, 0, top_alpha), QColor(0, 0, 0, bottom_alpha), strength
            )
            painter.setBrush(gradient)

        painter.drawPath(path)

    def _paint_outer_outline(
        self,
        painter: QPainter,
        rect: QRectF,
        radius: float,
        is_down: bool,
        under_mouse: bool,
        style: SurfaceStyle = SurfaceStyle.EMBOSSED,
        strength: float = 1.0,
    ) -> None:
        """Paint an outer outline with a top-to-bottom gradient."""
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        if style == SurfaceStyle.EMBOSSED:
            if is_dark_theme():
                top_alpha, bottom_alpha = _EMBOSSED_OUTER_OUTLINE_ALPHAS_DARK
            elif under_mouse and not is_down:
                top_alpha, bottom_alpha = _EMBOSSED_OUTER_OUTLINE_ALPHAS_HOVER_LIGHT
            else:
                top_alpha, bottom_alpha = _EMBOSSED_OUTER_OUTLINE_ALPHAS_LIGHT
            _set_stops(
                gradient, QColor(0, 0, 0, top_alpha), QColor(0, 0, 0, bottom_alpha), strength
            )
        elif style == SurfaceStyle.DEBOSSED:
            top_alpha, bottom_alpha = (
                _DEBOSSED_OUTER_OUTLINE_ALPHAS_DARK
                if is_dark_theme()
                else _DEBOSSED_OUTER_OUTLINE_ALPHAS_LIGHT
            )
            _set_stops(
                gradient,
                QColor(255, 255, 255, top_alpha),
                QColor(255, 255, 255, bottom_alpha),
                strength,
            )

        pen = QPen()
        pen.setWidth(1)
        pen.setBrush(gradient)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

    def _paint_inner_outline(
        self,
        painter: QPainter,
        rect: QRectF,
        radius: float,
        is_down: bool,
        style: SurfaceStyle = SurfaceStyle.EMBOSSED,
        strength: float = 1.0,
    ) -> None:
        """Paint an inner outline with a top-to-bottom gradient."""
        path = QPainterPath()
        inset = 1
        inner_rect = rect.adjusted(inset, inset, -inset, -inset)
        inner_radius = max(radius - inset, 0.0)
        path.addRoundedRect(inner_rect, inner_radius, inner_radius)

        gradient = QLinearGradient(
            rect.topLeft() if not is_down else rect.bottomLeft(),
            rect.bottomLeft() if not is_down else rect.topLeft(),
        )
        if style == SurfaceStyle.EMBOSSED:
            top_alpha, bottom_alpha = (
                _EMBOSSED_INNER_OUTLINE_ALPHAS_DARK
                if is_dark_theme()
                else _EMBOSSED_INNER_OUTLINE_ALPHAS_LIGHT
            )
            _set_stops(
                gradient,
                QColor(255, 255, 255, top_alpha),
                QColor(255, 255, 255, bottom_alpha),
                strength,
            )
        elif style == SurfaceStyle.DEBOSSED:
            top_alpha, bottom_alpha = (
                _DEBOSSED_INNER_OUTLINE_ALPHAS_DARK
                if is_dark_theme()
                else _DEBOSSED_INNER_OUTLINE_ALPHAS_LIGHT
            )
            _set_stops(
                gradient, QColor(0, 0, 0, top_alpha), QColor(0, 0, 0, bottom_alpha), strength
            )

        pen = QPen()
        pen.setWidth(1)
        pen.setBrush(gradient)
        painter.setPen(pen)
        painter.drawPath(path)

    def paint_capsule(
        self,
        painter: QPainter,
        rect: QRect,
        radius: float,
        primary_color: QColor,
        border_color: QColor | None,
        highlight_color: QColor,
        is_down: bool = False,
        is_hovered: bool = False,
        is_colorless: bool = False,
        border_width: int = 2,
    ) -> None:
        """Paint a capsule."""
        fill_color = highlight_color if is_down else primary_color
        if is_down:
            border = primary_color
        elif is_hovered:
            border = highlight_color
        else:
            border = border_color
        shadow_source_color = border_color if border_color is not None else fill_color
        self._paint_capsule_body(
            painter,
            rect,
            radius,
            fill_color,
            border,
            shadow_source_color,
            is_colorless,
            border_width,
        )
        if border_color is None:
            self._paint_capsule_highlight(painter, rect, radius, fill_color, is_down, is_colorless)

    def paint_dashed_capsule(
        self,
        painter: QPainter,
        rect: QRect,
        radius: float,
        fill_color: QColor | None,
        line_color: QColor,
    ) -> None:
        """Paint a capsule's shape as a dashed outline."""
        pen = QPen(line_color, _DASHED_CAPSULE_LINE_WIDTH)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        pen.setDashPattern(_DASHED_CAPSULE_PATTERN)
        inset = _DASHED_CAPSULE_LINE_WIDTH / 2
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(pen)
        painter.setBrush(fill_color if fill_color is not None else Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(
            QRectF(rect).adjusted(inset, inset, -inset, -inset), radius - inset, radius - inset
        )
        painter.restore()

    def _paint_capsule_body(
        self,
        painter: QPainter,
        rect: QRect,
        radius: float,
        fill_color: QColor,
        border_color: QColor | None,
        shadow_source_color: QColor,
        is_colorless: bool,
        border_width: int,
    ) -> None:
        """Paint a capsule's shadow tinted by its source color, optional border, and fill."""
        dpr = painter.device().devicePixelRatioF()
        layer = QImage(rect.size() * dpr, QImage.Format.Format_ARGB32_Premultiplied)
        layer.setDevicePixelRatio(dpr)
        layer.fill(Qt.GlobalColor.transparent)
        layer_painter = QPainter(layer)
        layer_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        layer_painter.setPen(Qt.PenStyle.NoPen)
        layer_rect = QRectF(0, 0, rect.width(), rect.height())

        def fill_inset(color: QColor, inset: int) -> None:
            layer_painter.setBrush(color)
            layer_painter.drawRoundedRect(
                layer_rect.adjusted(inset, inset, -inset, -inset), radius - inset, radius - inset
            )

        fill_inset(_capsule_shadow_color(shadow_source_color, is_colorless), 0)
        # Replace what's under each part so light fills don't bleed through the shadow's corners
        layer_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        if border_color is None:
            fill_inset(fill_color, 1)
        else:
            fill_inset(border_color, 1)
            fill_inset(fill_color, 1 + border_width)
        layer_painter.end()
        painter.drawImage(rect.topLeft(), layer)

    def _paint_capsule_highlight(
        self,
        painter: QPainter,
        rect: QRect,
        radius: float,
        fill_color: QColor,
        is_down: bool,
        is_colorless: bool,
    ) -> None:
        """Paint an outline highlight inside a capsule's shadow."""
        highlight_rect = QRectF(rect).adjusted(1.5, 1.5, -1.5, -1.5)
        highlight_radius = radius - 1.5
        gradient = QLinearGradient(
            highlight_rect.bottomLeft() if is_down else highlight_rect.topLeft(),
            highlight_rect.topLeft() if is_down else highlight_rect.bottomLeft(),
        )
        is_dark = is_dark_theme()
        is_plain_white = is_colorless and not is_dark
        if is_plain_white:
            gradient.setColorAt(0.0, _COLORLESS_HIGHLIGHT_TOP_LIGHT)
            gradient.setColorAt(1.0, _COLORLESS_HIGHLIGHT_BOTTOM_LIGHT)
        elif is_colorless:
            gradient.setColorAt(0.0, _COLORLESS_HIGHLIGHT_TOP_DARK)
            gradient.setColorAt(
                0.5, blend(_COLORLESS_HIGHLIGHT_TOP_DARK, _CAPSULE_HIGHLIGHT_BOTTOM, 0.5)
            )
            gradient.setColorAt(1.0, _COLORLESS_HIGHLIGHT_BOTTOM_DARK)
        else:
            gradient.setColorAt(0.0, _CAPSULE_HIGHLIGHT_TOP)
            gradient.setColorAt(1.0, _CAPSULE_HIGHLIGHT_BOTTOM)
        pen = QPen()
        pen.setWidth(1)
        pen.setBrush(gradient)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(pen)
        if is_plain_white:
            painter.drawRoundedRect(highlight_rect, highlight_radius, highlight_radius)
        else:
            min_opacity, max_opacity = (
                _CAPSULE_HIGHLIGHT_OPACITY_MIN,
                _CAPSULE_HIGHLIGHT_OPACITY_MAX,
            )
            opacity = min_opacity + (max_opacity - min_opacity) * _perceived_lightness(fill_color)
            painter.setOpacity(opacity * fill_color.alphaF())
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SoftLight)
            painter.drawRoundedRect(highlight_rect, highlight_radius, highlight_radius)
            if not is_dark:
                # Light theme capsules get an extra white highlight on top of the soft light
                painter.setOpacity(_CAPSULE_EXTRA_HIGHLIGHT_OPACITY_LIGHT)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
                painter.drawRoundedRect(highlight_rect, highlight_radius, highlight_radius)
            else:
                # Soft light barely brightens light fills, so they get extra white in the dark theme
                min_lightness = _CAPSULE_EXTRA_HIGHLIGHT_THRESHOLD_DARK
                extra = (_perceived_lightness(fill_color) - min_lightness) / (1 - min_lightness)
                if extra > 0:
                    painter.setOpacity(extra * _CAPSULE_EXTRA_HIGHLIGHT_OPACITY_DARK)
                    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
                    painter.drawRoundedRect(highlight_rect, highlight_radius, highlight_radius)
        painter.restore()

    def paint_image(self, painter: QPainter, rect: QRect, radius: int, image_brush: QBrush) -> None:
        """Paint an image with rounded corners and highlight and shadow outlines."""
        opacity = painter.opacity()
        width, height = rect.width(), rect.height()
        bounds = QRectF(0, 0, width, height)
        highlight_path = _outline_path(bounds.adjusted(1, 1, -1, -1), radius - 1, 1)
        painter.save()
        painter.translate(rect.topLeft())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setPen(Qt.PenStyle.NoPen)

        # Inset only halfway into the shadow outline to prevent a seam when anti-aliasing is applied
        painter.setBrush(image_brush)
        painter.drawPath(rounded_rect_path(bounds.adjusted(0.5, 0.5, -0.5, -0.5), radius - 0.5))

        # Pre-highlight background for dark images and alpha backgrounds
        painter.fillPath(highlight_path, IMAGE_HIGHLIGHT)

        # Highlight outline
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Screen)
        painter.setOpacity(opacity * IMAGE_SCREEN)
        painter.fillPath(highlight_path, image_brush)
        painter.setOpacity(opacity)
        is_dark = is_dark_theme()
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        if not is_dark:
            painter.fillPath(highlight_path, IMAGE_EXTRA_HIGHLIGHT_LIGHT)

        # Shadow outline
        shadow_brush = _image_shadow_brush(
            image_brush,
            width,
            height,
            radius,
            painter.device().devicePixelRatioF(),
            IMAGE_SHADOW_DARK if is_dark else IMAGE_SHADOW_LIGHT,
        )
        painter.fillPath(_outline_path(bounds, radius, 1), shadow_brush)
        painter.restore()

    def paint_focus_ring(
        self,
        painter: QPainter,
        rect: QRect,
        radius: float = RADIUS,
        square_edges: Qt.Edge | None = None,
    ) -> None:
        """Paint a colored focus ring outline."""
        self._paint_ring(painter, rect, radius, Palette.accent(), square_edges)

    def paint_invalid_ring(self, painter: QPainter, rect: QRect, radius: float = RADIUS) -> None:
        """Paint a red ring outline to indicate invalid widget contents."""
        self._paint_ring(
            painter, rect, radius, QColor.fromString(get_ui_color(ColorType.PRIMARY, UiColor.RED))
        )

    def _paint_ring(
        self,
        painter: QPainter,
        rect: QRect,
        radius: float,
        color: QColor,
        square_edges: Qt.Edge | None = None,
    ) -> None:
        rectf = QRectF(rect).adjusted(1, 1, -1, -1)
        path = rounded_rect_path(rectf, radius, square_edges)

        pen = QPen(color)
        pen.setWidthF(2.0)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        painter.restore()
