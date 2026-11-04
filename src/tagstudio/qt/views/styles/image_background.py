# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PIL import ImageFilter, ImageQt
from PySide6.QtCore import QRect
from PySide6.QtGui import QColor, QPainter, QPixmap

from tagstudio.qt.views.styles.stylesheets import WINDOW_BG_SHADE_DARK, is_dark_theme

_BACKGROUND_HEIGHT_SCALE = 0.75


def _blurred(pixmap: QPixmap, radius: float) -> QPixmap:
    """Return a blurred copy of a QPixmap."""
    image = ImageQt.fromqpixmap(pixmap).filter(ImageFilter.GaussianBlur(radius))
    return QPixmap.fromImage(ImageQt.ImageQt(image))


class ImageBackground:
    """An image across the top of a window."""

    def __init__(self, pixmap: QPixmap, blur_radius: float = 0) -> None:
        self._image = (_blurred(pixmap, blur_radius) if blur_radius else pixmap).toImage()
        self.opacity = 1.0

    def paint(self, painter: QPainter, rect: QRect, top: int = 0) -> None:
        """Shade a given rect, then draw the image starting at a given y position."""
        width = rect.width()
        aspect_ratio = self._image.height() / self._image.width()
        height = round(width * aspect_ratio * _BACKGROUND_HEIGHT_SCALE)
        painter.save()
        if is_dark_theme():
            painter.fillRect(rect, QColor(WINDOW_BG_SHADE_DARK))
        painter.setOpacity(self.opacity)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawImage(QRect(rect.left(), top, width, height), self._image)
        top_edge = QRect(0, 0, self._image.width(), 1)
        painter.drawImage(
            QRect(rect.left(), rect.top(), width, top - rect.top()), self._image, top_edge
        )
        painter.restore()
