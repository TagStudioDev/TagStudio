# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import math
from functools import lru_cache

from PySide6.QtCore import QByteArray, QRect, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

from tagstudio.core.constants import TAG_ARCHIVED, TAG_FAVORITE
from tagstudio.qt.resource_manager import ResourceManager

# TODO: Replace with custom tag icons once tags can set their own
_TAG_ICONS: dict[int, str] = {
    TAG_FAVORITE: "favorite_icon",
    TAG_ARCHIVED: "archived_icon",
}

ICON_SIZE = 18  # Leaves 3px around the icon in a tag's height
# Icons shrink by 2px for each sharper corner they reach, stepped from a circle down to a square
_CORNERS = (ICON_SIZE / 2, 6, 3, 0)
_SHRINK_STEP = 2
_FIT_DENSITY = 6  # Pixels per point when checking where an icon reaches


def tag_icon(tag_id: int) -> bytes | None:
    """The SVG icon for a tag, if it has one."""
    name = _TAG_ICONS.get(tag_id)
    if name is None:
        return None
    icon = ResourceManager().get(name)
    assert isinstance(icon, bytes)
    return icon


def _icon_rect(renderer: QSvgRenderer, size: float, scale: float) -> QRectF:
    """Where an icon is drawn to fit centered in a square."""
    view = renderer.viewBoxF()
    fit = size / max(view.width(), view.height())
    width, height = view.width() * fit, view.height() * fit
    return QRectF(
        (size - width) / 2 * scale, (size - height) / 2 * scale, width * scale, height * scale
    )


@lru_cache(maxsize=32)
def _icon_shrink(icon: bytes, corner: float) -> int:
    """How much smaller to draw an icon so it fits a rounded square."""
    renderer = QSvgRenderer(QByteArray(icon))
    side = ICON_SIZE * _FIT_DENSITY
    image = QImage(side, side, QImage.Format.Format_Alpha8)
    image.fill(0)
    painter = QPainter(image)
    renderer.render(painter, _icon_rect(renderer, ICON_SIZE, _FIT_DENSITY))
    painter.end()

    data = bytes(image.constBits())
    stride = image.bytesPerLine()
    center = side / 2
    # Each covered pixel's distance from the center along both axes, in points
    reaches = [
        (abs(x + 0.5 - center) / _FIT_DENSITY, abs(y + 0.5 - center) / _FIT_DENSITY)
        for y in range(side)
        for x, alpha in enumerate(data[y * stride : y * stride + side])
        if alpha > 127
    ]

    def fits(corner: float) -> bool:
        straight = ICON_SIZE / 2 - corner
        return all(
            math.hypot(dx - straight, dy - straight) <= corner
            for dx, dy in reaches
            if dx > straight and dy > straight
        )

    corners = [c for c in _CORNERS if c <= corner]
    for step, rounded_corner in enumerate(corners):
        if fits(rounded_corner):
            return step * _SHRINK_STEP
    return (len(corners) - 1) * _SHRINK_STEP


@lru_cache(maxsize=32)
def _icon_image(icon: bytes, size: int, pixel_ratio: float, rgba: int) -> QImage:
    """An icon filled with one color, centered in a square of a given size."""
    renderer = QSvgRenderer(QByteArray(icon))
    side = math.ceil(size * pixel_ratio)
    image = QImage(side, side, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer.render(painter, _icon_rect(renderer, size, pixel_ratio))
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(image.rect(), QColor.fromRgba(rgba))
    painter.end()
    image.setDevicePixelRatio(pixel_ratio)
    return image


def icon_shrink(icon: bytes, slot_size: int, radius: float) -> int:
    """How much smaller an icon is drawn in a square slot with a given corner radius."""
    margin = (slot_size - ICON_SIZE) / 2
    return _icon_shrink(icon, max(radius - margin, 0))


def paint_icon(painter: QPainter, slot: QRect, radius: float, icon: bytes, color: QColor) -> None:
    """Paint an icon centered in a square with a given corner radius."""
    size = ICON_SIZE - icon_shrink(icon, slot.height(), radius)
    inset = (slot.height() - size) / 2
    image = _icon_image(icon, size, painter.device().devicePixelRatioF(), color.rgba())
    painter.drawImage(QRectF(slot.left() + inset, slot.top() + inset, size, size), image)
