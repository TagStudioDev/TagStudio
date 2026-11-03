# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from PIL import Image, ImageQt
from PySide6.QtCore import QByteArray, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QGuiApplication, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from tagstudio.qt.views.styles.palette import Palette

# TODO: Consolidate the built-in QT theme values with the values
# here, in enums.py, and in palette.py.
_THEME_DARK_FG = QColor(255, 255, 255, 120)
_THEME_LIGHT_FG = QColor(0, 0, 0, 220)


def theme_foreground_color() -> QColor:
    """Return a translucent foreground color for icons and hint text in the current theme."""
    if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark:
        return QColor(255, 255, 255, 120)
    return QColor(0, 0, 0, 120)


def svg_color_overlay(
    svg: bytes, color: QColor, device_pixel_ratio: float, size: QSize | None = None
) -> QPixmap:
    """An SVG overlaid with a color."""
    renderer = QSvgRenderer(QByteArray(svg))
    size = size if size is not None else renderer.defaultSize()
    bounds = QRectF(0, 0, size.width(), size.height())

    pixmap = QPixmap(size * device_pixel_ratio)
    pixmap.setDevicePixelRatio(device_pixel_ratio)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter, bounds)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(bounds, color)
    painter.end()
    return pixmap


def toggle_icon(svg: bytes, checked_svg: bytes, size: QSize, device_pixel_ratio: float) -> QIcon:
    """An SVG icon in the foreground color, and another in the accent color while checked."""
    icon = QIcon(svg_color_overlay(svg, theme_foreground_color(), device_pixel_ratio, size))
    icon.addPixmap(
        svg_color_overlay(checked_svg, Palette.accent_alt(), device_pixel_ratio, size),
        QIcon.Mode.Normal,
        QIcon.State.On,
    )
    return icon


def pixmap_color_overlay(pixmap: QPixmap, color: QColor) -> QPixmap:
    """A pixmap overlaid with a color."""
    overlaid = QPixmap(pixmap.size())
    overlaid.setDevicePixelRatio(pixmap.devicePixelRatio())
    overlaid.fill(Qt.GlobalColor.transparent)
    painter = QPainter(overlaid)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(overlaid.rect(), color)
    painter.end()
    return overlaid


def image_theme_color_overlay(
    image: Image.Image, inverse: bool = False, use_alpha: bool = True
) -> QPixmap:
    """Overlay the current foreground theme color onto an image.

    Args:
        image (Image): The PIL Image object to apply an overlay to.
        inverse (bool): Option to invert the overlay color relative to the current theme.
        use_alpha (bool): Option to use the theme's translucent foreground color.
    """
    is_dark = QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
    if inverse:
        is_dark = not is_dark
    color = QColor(_THEME_DARK_FG if is_dark else _THEME_LIGHT_FG)
    if not use_alpha:
        color.setAlpha(255)
    return image_color_overlay(image, color)


def image_color_overlay(image: Image.Image, color: QColor) -> QPixmap:
    """Apply a color overlay on top of an image using the image's alpha channel as a mask.

    Args:
        image (Image): The PIL Image object to apply an overlay to.
        color (QColor): The color of the overlay.
    """
    return pixmap_color_overlay(QPixmap.fromImage(ImageQt.ImageQt(image)), color)
