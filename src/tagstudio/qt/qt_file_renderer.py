# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

import math
from functools import cache, lru_cache
from pathlib import Path

from PIL import Image, ImageQt
from PySide6.QtCore import QObject, QRectF, Signal
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPen, QPixmap, Qt

from tagstudio.core.enums import Theme
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.media_types import slugify
from tagstudio.previews.file_renderer import FileRenderer, RenderResult
from tagstudio.qt.app_settings import AppSettings
from tagstudio.qt.cache_manager import CacheManager
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.styles.palette import ColorType, UiColor, get_ui_color
from tagstudio.qt.views.styles.stylesheets import OUTLINE_WIDTH, RADIUS


def _letterbox(image: QImage) -> QImage:
    """Center a non-square image over a gradient blended from its corner colors."""
    width, height = image.width(), image.height()
    side = max(width, height)
    colors = [image.pixelColor(x, y) for y in (0, height - 1) for x in (0, width - 1)]
    corners = Image.new("RGB", (2, 2))
    corners.putdata([(c.red(), c.green(), c.blue()) for c in colors])
    background = ImageQt.ImageQt(corners.resize((side, side), Image.Resampling.BICUBIC)).copy()

    painter = QPainter(background)
    painter.drawImage((side - width) // 2, (side - height) // 2, image)
    painter.end()
    return background


def paint_fallback_icon_border(
    painter: QPainter, rect: QRectF, color: QColor, pixel_ratio: float
) -> None:
    """Paint the thick rounded border for fallback icons."""
    width = (OUTLINE_WIDTH + 2) * pixel_ratio
    inset = width / 2
    radius = RADIUS * pixel_ratio - inset
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(color, width))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(rect.adjusted(inset, inset, -inset, -inset), radius, radius)


@cache
def _resource_image(name: str) -> QImage:
    return ImageQt.ImageQt(ResourceManager().get(name)).copy()


def _media_icon(filepath: Path) -> str:
    """The icon resource name for the most specific media group of a file."""
    resources = ResourceManager()
    for group in FileRenderer.media_groups(filepath):
        if resources.get(slugify(group), silent_fail=True):
            return slugify(group)
    return "file_generic"


@lru_cache(maxsize=32)
def _icon(name: str, color: UiColor, theme: Theme, side: int, pixel_ratio: float) -> QImage:
    """A default icon centered on a background."""
    is_dark = theme == Theme.DARK
    background = get_ui_color(ColorType.DARK_ACCENT if is_dark else ColorType.PRIMARY, color)
    foreground = get_ui_color(ColorType.BORDER if is_dark else ColorType.LIGHT_ACCENT, color)

    glyph_side = int(side / 1.75)
    glyph = _resource_image(name).scaled(
        glyph_side,
        glyph_side,
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    glyph = glyph.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
    painter = QPainter(glyph)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(glyph.rect(), QColor(foreground))
    painter.end()

    image = QImage(side, side, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(background))
    painter.drawRoundedRect(QRectF(image.rect()), RADIUS * pixel_ratio, RADIUS * pixel_ratio)
    painter.drawImage((side - glyph_side) // 2, (side - glyph_side) // 2, glyph)
    painter.end()
    return image


def _with_corner_icon(image: QImage, name: str) -> QImage:
    """Draw an icon in the upper left corner of an image."""
    image = image.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
    side = min(image.width(), image.height())
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    painter.drawImage(QRectF(side / 18, side / 18, side / 5, side / 5), _resource_image(name))
    painter.end()
    return image


class QtFileRenderer(QObject):
    """A Qt-specific wrapper for rendering image previews and thumbnails from files."""

    updated = Signal(float, QPixmap, Path, object)  # Timestamp, image, path, border color

    def __init__(self, library: Library, settings: AppSettings) -> None:
        super().__init__()
        self.renderer = FileRenderer(library, settings)
        self.theme = (
            Theme.DARK
            if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
            else Theme.LIGHT
        )
        self._theme_color = UiColor.THEME_DARK if self.theme == Theme.DARK else UiColor.THEME_LIGHT

    def _border_color(self, color: UiColor) -> QColor:
        color_type = ColorType.PRIMARY if self.theme == Theme.DARK else ColorType.LIGHT_ACCENT
        return QColor(get_ui_color(color_type, color))

    def loading_image(self, size: tuple[int, int], pixel_ratio: float) -> QPixmap:
        """The image to show while a thumbnail or preview renders."""
        side = math.ceil(max(size[0], size[1]) * pixel_ratio)
        pixmap = QPixmap.fromImage(
            _icon("thumb_loading", self._theme_color, self.theme, side, pixel_ratio)
        )
        pixmap.setDevicePixelRatio(pixel_ratio)
        return pixmap

    def _placeholder(
        self,
        cache: CacheManager | None,
        filepath: Path,
        side: int,
        pixel_ratio: float,
        date_modified: float | None,
    ) -> QImage | None:
        """What to show while a file's preview renders, or `None` if it won't render."""
        renderer = FileRenderer.find_renderer(filepath)
        if (
            renderer is None
            or not filepath.is_file()
            or FileRenderer.previously_failed(filepath, self.theme, date_modified)
        ):
            return None
        if renderer.has_small_variant:
            # The thumbnail looks different, so stay blank until the preview renders
            blank = QImage(side, side, QImage.Format.Format_ARGB32_Premultiplied)
            blank.fill(Qt.GlobalColor.transparent)
            return blank
        cached = FileRenderer.cached_thumbnail(cache, filepath, self.theme, date_modified)
        if cached is None:
            return _icon("thumb_loading", self._theme_color, self.theme, side, pixel_ratio)
        return ImageQt.ImageQt(cached)

    def render(
        self,
        cache: CacheManager | None,
        timestamp: float,
        filepath: Path | str,
        size: tuple[int, int],
        pixel_ratio: float,
        is_placeholder: bool = False,
        is_thumb: bool = False,
        date_modified: float | None = None,
    ):
        filepath = Path(filepath)
        side = math.ceil(max(size[0], size[1]) * pixel_ratio)
        result = RenderResult(None)
        if not is_placeholder:
            result = self.renderer.render(
                cache=cache,
                filepath=filepath,
                size=size,
                dpi_scale=pixel_ratio,
                theme=self.theme,
                is_thumb=is_thumb,
                date_modified=date_modified,
            )

        image = None if result.image is None else ImageQt.ImageQt(result.image)
        if is_placeholder:
            image = self._placeholder(cache, filepath, side, pixel_ratio, date_modified)

        border_color = None
        if image is None:
            is_missing = result.is_unlinked or not filepath.is_file()
            cached = None
            if is_missing and not is_thumb:
                cached = FileRenderer.cached_thumbnail(cache, filepath, self.theme, date_modified)
            if cached is not None:
                image = ImageQt.ImageQt(cached)
            else:
                color = UiColor.RED if is_missing else self._theme_color
                name = "broken_link_icon" if is_missing else _media_icon(filepath)
                image = _icon(name, color, self.theme, side, pixel_ratio)
                border_color = self._border_color(color)
                if is_thumb:
                    image = image.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
                    painter = QPainter(image)
                    paint_fallback_icon_border(
                        painter, QRectF(image.rect()), border_color, pixel_ratio
                    )
                    painter.end()
        elif is_thumb and image.width() != image.height():
            image = _letterbox(image)

        if result.is_unlinked and border_color is None:
            image = _with_corner_icon(image, "unlinked_stat")
        elif result.is_ignored:
            image = _with_corner_icon(image, "ignored")
        pixmap = QPixmap.fromImage(image)
        pixmap.setDevicePixelRatio(pixel_ratio)
        self.updated.emit(timestamp, pixmap, filepath, border_color)
