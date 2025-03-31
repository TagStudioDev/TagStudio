# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import contextlib
import hashlib
import math
import struct
import zipfile
from copy import deepcopy
from io import BytesIO
from pathlib import Path
from warnings import catch_warnings

import cv2
import numpy as np
import rawpy
import structlog
from cv2.typing import MatLike
from mutagen import MutagenError, flac, id3, mp4
from PIL import (
    Image,
    ImageChops,
    ImageDraw,
    ImageEnhance,
    ImageFile,
    ImageFont,
    ImageOps,
    ImageQt,
    UnidentifiedImageError,
)
from PIL.Image import DecompressionBombError
from pillow_heif import register_avif_opener, register_heif_opener
from PySide6.QtCore import (
    QBuffer,
    QFile,
    QFileDevice,
    QIODeviceBase,
    QObject,
    QSize,
    QSizeF,
    Qt,
    Signal,
)
from PySide6.QtGui import QGuiApplication, QImage, QPainter, QPixmap
from PySide6.QtPdf import QPdfDocument, QPdfDocumentRenderOptions
from PySide6.QtSvg import QSvgRenderer
from vtf2img import Parser

from tagstudio.core.constants import (
    FONT_SAMPLE_SIZES,
    FONT_SAMPLE_TEXT,
    THUMB_CACHE_NAME,
    TS_FOLDER_NAME,
)
from tagstudio.core.exceptions import NoRendererError
from tagstudio.core.media_types import MediaCategories, MediaType
from tagstudio.core.palette import ColorType, UiColor, get_ui_color
from tagstudio.core.utils.encoding import detect_char_encoding
from tagstudio.qt.cache_manager import CacheManager
from tagstudio.qt.helpers.blender_thumbnailer import blend_thumb
from tagstudio.qt.helpers.color_overlay import theme_fg_overlay
from tagstudio.qt.helpers.file_tester import is_readable_video
from tagstudio.qt.helpers.gradient import four_corner_gradient
from tagstudio.qt.helpers.image_effects import replace_transparent_pixels
from tagstudio.qt.helpers.text_wrapper import wrap_full_text
from tagstudio.qt.helpers.vendored.pydub.audio_segment import (
    _AudioSegment as AudioSegment,
)
from tagstudio.qt.resource_manager import ResourceManager

ImageFile.LOAD_TRUNCATED_IMAGES = True

logger = structlog.get_logger(__name__)
Image.MAX_IMAGE_PIXELS = None
register_heif_opener()
register_avif_opener()

try:
    import pillow_jxl  # noqa: F401 # pyright: ignore[reportUnusedImport]
except ImportError:
    logger.exception('[ThumbRenderer] Could not import the "pillow_jxl" module')


class ThumbRenderer(QObject):
    """A class for rendering image and file thumbnails."""

    rm: ResourceManager = ResourceManager()
    cache: CacheManager = CacheManager()
    updated = Signal(float, QPixmap, QSize, Path, str)
    updated_ratio = Signal(float)

    cached_img_res: int = 256  # TODO: Pull this from config
    cached_img_ext: str = ".webp"  # TODO: Pull this from config

    last_cache_folder: Path | None = None

    def __init__(self, library) -> None:
        """Initialize the class."""
        super().__init__()
        self.lib = library
        ThumbRenderer.cache.set_library(self.lib)

        # Cached thumbnail elements.
        # Key: Size + Pixel Ratio Tuple + Radius Scale
        #      (Ex. (512, 512, 1.25, 4))
        self.thumb_masks: dict[tuple[int, int, float, float], Image.Image] = {}
        self.raised_edges: dict[tuple[int, int, float], tuple[Image.Image, Image.Image]] = {}

        # Key: ("name", UiColor, 512, 512, 1.25)
        self.icons: dict[tuple[str, UiColor, int, int, float], Image.Image] = {}

    def _get_resource_id(self, url: Path) -> str:
        """Return the name of the icon resource to use for a file type.

        Special terms will return special resources.

        Args:
            url (Path): The file url to assess. "$LOADING" will return the loading graphic.
        """
        ext = url.suffix.lower()
        types: set[MediaType] = MediaCategories.get_types(ext, mime_fallback=True)

        # Manual icon overrides.
        if ext in {".gif", ".vtf"}:
            return MediaType.IMAGE
        elif ext in {".dll", ".pyc", ".o", ".dylib"}:
            return MediaType.PROGRAM
        elif ext in {".mscz"}:  # noqa: SIM114
            return MediaType.TEXT

        # Loop though the specific (non-IANA) categories and return the string
        # name of the first matching category found.
        for cat in MediaCategories.ALL_CATEGORIES:
            if not cat.is_iana and cat.media_type in types:
                return cat.media_type.value

        # If the type is broader (IANA registered) then search those types.
        for cat in MediaCategories.ALL_CATEGORIES:
            if cat.is_iana and cat.media_type in types:
                return cat.media_type.value

        return "file_generic"

    def _get_mask(
        self, size: tuple[int, int], pixel_ratio: float, scale_radius: bool = False
    ) -> Image.Image:
        """Return a thumbnail mask given a size, pixel ratio, and radius scaling option.

        If one is not already cached, a new one will be rendered.

        Args:
            size (tuple[int, int]): The size of the graphic.
            pixel_ratio (float): The screen pixel ratio.
            scale_radius (bool): Option to scale the radius up (Used for Preview Panel).
        """
        thumb_scale: int = 512
        radius_scale: float = 1
        if scale_radius:
            radius_scale = max(size[0], size[1]) / thumb_scale

        item: Image.Image | None = self.thumb_masks.get((*size, pixel_ratio, radius_scale))
        if not item:
            item = self._render_mask(size, pixel_ratio, radius_scale)
            self.thumb_masks[(*size, pixel_ratio, radius_scale)] = item
        return item

    def _get_edge(
        self, size: tuple[int, int], pixel_ratio: float
    ) -> tuple[Image.Image, Image.Image]:
        """Return a thumbnail edge given a size, pixel ratio, and radius scaling option.

        If one is not already cached, a new one will be rendered.

        Args:
            size (tuple[int, int]): The size of the graphic.
            pixel_ratio (float): The screen pixel ratio.
        """
        item: tuple[Image.Image, Image.Image] | None = self.raised_edges.get((*size, pixel_ratio))
        if not item:
            item = self._render_edge(size, pixel_ratio)
            self.raised_edges[(*size, pixel_ratio)] = item
        return item

    def _get_icon(
        self, name: str, color: UiColor, size: tuple[int, int], pixel_ratio: float = 1.0
    ) -> Image.Image:
        """Return an icon given a size, pixel ratio, and radius scaling option.

        Args:
            name (str): The name of the icon resource. "thumb_loading" will not draw a border.
            color (str): The color to use for the icon.
            size (tuple[int,int]): The size of the icon.
            pixel_ratio (float): The screen pixel ratio.
        """
        draw_border: bool = True
        if name == "thumb_loading":
            draw_border = False

        item: Image.Image | None = self.icons.get((name, color, *size, pixel_ratio))
        if not item:
            item_flat: Image.Image = self._render_icon(name, color, size, pixel_ratio, draw_border)
            edge: tuple[Image.Image, Image.Image] = self._get_edge(size, pixel_ratio)
            item = self._apply_edge(item_flat, edge, faded=True)
            self.icons[(name, color, *size, pixel_ratio)] = item
        return item

    def _render_mask(
        self, size: tuple[int, int], pixel_ratio: float, radius_scale: float = 1
    ) -> Image.Image:
        """Render a thumbnail mask graphic.

        Args:
            size (tuple[int,int]): The size of the graphic.
            pixel_ratio (float): The screen pixel ratio.
            radius_scale (float): The scale factor of the border radius (Used by Preview Panel).
        """
        smooth_factor: int = 2
        radius_factor: int = 8

        im: Image.Image = Image.new(
            mode="L",
            size=tuple([d * smooth_factor for d in size]),  # type: ignore
            color="black",
        )
        draw = ImageDraw.Draw(im)
        draw.rounded_rectangle(
            (0, 0) + tuple([d - 1 for d in im.size]),
            radius=math.ceil(radius_factor * smooth_factor * pixel_ratio * radius_scale),
            fill="white",
        )
        im = im.resize(
            size,
            resample=Image.Resampling.BILINEAR,
        )
        return im

    def _render_edge(
        self, size: tuple[int, int], pixel_ratio: float
    ) -> tuple[Image.Image, Image.Image]:
        """Render a thumbnail edge graphic.

        Args:
            size (tuple[int,int]): The size of the graphic.
            pixel_ratio (float): The screen pixel ratio.
        """
        smooth_factor: int = 2
        radius_factor: int = 8
        width: int = math.floor(pixel_ratio * 2)

        # Highlight
        im_hl: Image.Image = Image.new(
            mode="RGBA",
            size=tuple([d * smooth_factor for d in size]),  # type: ignore
            color="#00000000",
        )
        draw = ImageDraw.Draw(im_hl)
        draw.rounded_rectangle(
            (width, width) + tuple([d - (width + 1) for d in im_hl.size]),
            radius=math.ceil((radius_factor * smooth_factor * pixel_ratio) - (pixel_ratio * 3)),
            fill=None,
            outline="white",
            width=width,
        )
        im_hl = im_hl.resize(
            size,
            resample=Image.Resampling.BILINEAR,
        )

        # Shadow
        im_sh: Image.Image = Image.new(
            mode="RGBA",
            size=tuple([d * smooth_factor for d in size]),  # type: ignore
            color="#00000000",
        )
        draw = ImageDraw.Draw(im_sh)
        draw.rounded_rectangle(
            (0, 0) + tuple([d - 1 for d in im_sh.size]),
            radius=math.ceil(radius_factor * smooth_factor * pixel_ratio),
            fill=None,
            outline="black",
            width=width,
        )
        im_sh = im_sh.resize(
            size,
            resample=Image.Resampling.BILINEAR,
        )

        return (im_hl, im_sh)

    def _render_icon(
        self,
        name: str,
        color: UiColor,
        size: tuple[int, int],
        pixel_ratio: float,
        draw_border: bool = True,
    ) -> Image.Image:
        """Render a thumbnail icon.

        Args:
            name (str): The name of the icon resource.
            color (UiColor): The color to use for the icon.
            size (tuple[int,int]): The size of the icon.
            pixel_ratio (float): The screen pixel ratio.
            draw_border (bool): Option to draw a border.
        """
        border_factor: int = 5
        smooth_factor: int = math.ceil(2 * pixel_ratio)
        radius_factor: int = 8
        icon_ratio: float = 1.75

        # Create larger blank image based on smooth_factor
        im: Image.Image = Image.new(
            "RGBA",
            size=tuple([d * smooth_factor for d in size]),  # type: ignore
            color="#00000000",
        )

        # Create solid background color
        bg: Image.Image = Image.new(
            "RGB",
            size=tuple([d * smooth_factor for d in size]),  # type: ignore
            color="#000000",
        )

        # Paste background color with rounded rectangle mask onto blank image
        im.paste(
            bg,
            (0, 0),
            mask=self._get_mask(
                tuple([d * smooth_factor for d in size]),  # type: ignore
                (pixel_ratio * smooth_factor),
            ),
        )

        # Draw rounded rectangle border
        if draw_border:
            draw = ImageDraw.Draw(im)
            draw.rounded_rectangle(
                (0, 0) + tuple([d - 1 for d in im.size]),
                radius=math.ceil(
                    (radius_factor * smooth_factor * pixel_ratio) + (pixel_ratio * 1.5)
                ),
                fill="black",
                outline="#FF0000",
                width=math.floor(
                    (border_factor * smooth_factor * pixel_ratio) - (pixel_ratio * 1.5)
                ),
            )

        # Resize image to final size
        im = im.resize(
            size,
            resample=Image.Resampling.BILINEAR,
        )
        fg: Image.Image = Image.new(
            "RGB",
            size=size,
            color="#00FF00",
        )

        # Get icon by name
        icon: Image.Image = self.rm.get(name)
        if not icon:
            icon = self.rm.get("file_generic")
            if not icon:
                icon = Image.new(mode="RGBA", size=(32, 32), color="magenta")

        # Resize icon to fit icon_ratio
        icon = icon.resize((math.ceil(size[0] // icon_ratio), math.ceil(size[1] // icon_ratio)))

        # Paste icon centered
        im.paste(
            im=fg.resize((math.ceil(size[0] // icon_ratio), math.ceil(size[1] // icon_ratio))),
            box=(
                math.ceil((size[0] - (size[0] // icon_ratio)) // 2),
                math.ceil((size[1] - (size[1] // icon_ratio)) // 2),
            ),
            mask=icon.getchannel(3),
        )

        # Apply color overlay
        im = self._apply_overlay_color(
            im,
            color,
        )

        return im

    def _apply_overlay_color(self, image: Image.Image, color: UiColor) -> Image.Image:
        """Apply a color overlay effect to an image based on its color channel data.

        Red channel for foreground, green channel for outline, none for background.

        Args:
            image (Image.Image): The image to apply an overlay to.
            color (UiColor): The name of the ColorType color to use.
        """
        bg_color: str = (
            get_ui_color(ColorType.DARK_ACCENT, color)
            if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
            else get_ui_color(ColorType.PRIMARY, color)
        )
        fg_color: str = (
            get_ui_color(ColorType.PRIMARY, color)
            if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
            else get_ui_color(ColorType.LIGHT_ACCENT, color)
        )
        ol_color: str = (
            get_ui_color(ColorType.BORDER, color)
            if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
            else get_ui_color(ColorType.LIGHT_ACCENT, color)
        )

        bg: Image.Image = Image.new(image.mode, image.size, color=bg_color)
        fg: Image.Image = Image.new(image.mode, image.size, color=fg_color)
        ol: Image.Image = Image.new(image.mode, image.size, color=ol_color)

        bg.paste(fg, (0, 0), mask=image.getchannel(0))
        bg.paste(ol, (0, 0), mask=image.getchannel(1))

        if image.mode == "RGBA":
            alpha_bg: Image.Image = bg.copy()
            alpha_bg.convert("RGBA")
            alpha_bg.putalpha(0)
            alpha_bg.paste(bg, (0, 0), mask=image.getchannel(3))
            bg = alpha_bg

        return bg

    def _apply_edge(
        self,
        image: Image.Image,
        edge: tuple[Image.Image, Image.Image],
        faded: bool = False,
    ) -> Image.Image:
        """Apply a given edge effect to an image.

        Args:
            image (Image.Image): The image to apply the edge to.
            edge (tuple[Image.Image, Image.Image]): The edge images to apply.
                Item 0 is the inner highlight, and item 1 is the outer shadow.
            faded (bool): Whether or not to apply a faded version of the edge.
                Used for light themes.
        """
        opacity: float = 1.0 if not faded else 0.8
        shade_reduction: float = (
            0 if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark else 0.3
        )
        im: Image.Image = image
        im_hl, im_sh = deepcopy(edge)

        # Configure and apply a soft light overlay.
        # This makes up the bulk of the effect.
        im_hl.putalpha(ImageEnhance.Brightness(im_hl.getchannel(3)).enhance(opacity))
        im.paste(ImageChops.soft_light(im, im_hl), mask=im_hl.getchannel(3))

        # Configure and apply a normal shading overlay.
        # This helps with contrast.
        im_sh.putalpha(
            ImageEnhance.Brightness(im_sh.getchannel(3)).enhance(max(0, opacity - shade_reduction))
        )
        im.paste(im_sh, mask=im_sh.getchannel(3))

        return im

    @staticmethod
    def _audio_album_thumb(filepath: Path, ext: str) -> Image.Image | None:
        """Return an album cover thumb from an audio file if a cover is present.

        Args:
            filepath (Path): The path of the file.
            ext (str): The file extension (with leading ".").
        """
        image: Image.Image | None = None
        try:
            if not filepath.is_file():
                raise FileNotFoundError

            artwork = None
            if ext in [".mp3"]:
                id3_tags: id3.ID3 = id3.ID3(filepath)
                id3_covers: list = id3_tags.getall("APIC")
                if id3_covers:
                    artwork = Image.open(BytesIO(id3_covers[0].data))
            elif ext in [".flac"]:
                flac_tags: flac.FLAC = flac.FLAC(filepath)
                flac_covers: list = flac_tags.pictures
                if flac_covers:
                    artwork = Image.open(BytesIO(flac_covers[0].data))
            elif ext in [".mp4", ".m4a", ".aac"]:
                mp4_tags: mp4.MP4 = mp4.MP4(filepath)
                mp4_covers: list = mp4_tags.get("covr")
                if mp4_covers:
                    artwork = Image.open(BytesIO(mp4_covers[0]))
            if artwork:
                image = artwork
        except (
            mp4.MP4MetadataError,
            mp4.MP4StreamInfoError,
            id3.ID3NoHeaderError,
            MutagenError,
        ) as e:
            logger.error("Couldn't read album artwork", path=filepath, error=type(e).__name__)
        return image

    @staticmethod
    def _audio_waveform_thumb(
        filepath: Path, ext: str, size: int, pixel_ratio: float
    ) -> Image.Image | None:
        """Render a waveform image from an audio file.

        Args:
            filepath (Path): The path of the file.
            ext (str): The file extension (with leading ".").
            size (tuple[int,int]): The size of the thumbnail.
            pixel_ratio (float): The screen pixel ratio.
        """
        # BASE_SCALE used for drawing on a larger image and resampling down
        # to provide an antialiased effect.
        base_scale: int = 2
        samples_per_bar: int = 3
        size_scaled: int = size * base_scale
        allow_small_min: bool = False
        im: Image.Image = None

        try:
            bar_count: int = min(math.floor((size // pixel_ratio) / 5), 64)
            audio: AudioSegment = AudioSegment.from_file(filepath, ext[1:])
            data = np.fromstring(audio._data, np.int16)  # type: ignore
            data_indices = np.linspace(1, len(data), num=bar_count * samples_per_bar)
            bar_margin: float = ((size_scaled / (bar_count * 3)) * base_scale) / 2
            line_width: float = ((size_scaled - bar_margin) / (bar_count * 3)) * base_scale
            bar_height: float = (size_scaled) - (size_scaled // bar_margin)

            count: int = 0
            maximum_item: int = 0
            max_array: list = []
            highest_line: int = 0

            for i in range(-1, len(data_indices)):
                d = data[math.ceil(data_indices[i]) - 1]
                if count < samples_per_bar:
                    count = count + 1
                    with catch_warnings(record=True):
                        if abs(d) > maximum_item:
                            maximum_item = abs(d)
                else:
                    max_array.append(maximum_item)

                    if maximum_item > highest_line:
                        highest_line = maximum_item

                    maximum_item = 0
                    count = 1

            line_ratio = max(highest_line / bar_height, 1)

            im = Image.new("RGB", (size_scaled, size_scaled), color="#000000")
            draw = ImageDraw.Draw(im)

            current_x = bar_margin
            for item in max_array:
                item_height = item / line_ratio

                # If small minimums are not allowed, raise all values
                # smaller than the line width to the same value.
                if not allow_small_min:
                    item_height = max(item_height, line_width)

                current_y = (bar_height - item_height + (size_scaled // bar_margin)) // 2

                draw.rounded_rectangle(
                    (
                        current_x,
                        current_y,
                        (current_x + line_width),
                        (current_y + item_height),
                    ),
                    radius=100 * base_scale,
                    fill=("#FF0000"),
                    outline=("#FFFF00"),
                    width=max(math.ceil(line_width / 6), base_scale),
                )

                current_x = current_x + line_width + bar_margin

            im.resize((size, size), Image.Resampling.BILINEAR)

        except Exception as e:
            logger.error("Couldn't render waveform", path=filepath.name, error=type(e).__name__)

        return im

    @staticmethod
    def _blender(filepath: Path) -> Image.Image:
        """Get an emended thumbnail from a Blender file, if a thumbnail is present.

        Args:
            filepath (Path): The path of the file.
        """
        bg_color: str = (
            "#1e1e1e"
            if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
            else "#FFFFFF"
        )
        im: Image.Image = None
        try:
            blend_image = blend_thumb(str(filepath))

            bg = Image.new("RGB", blend_image.size, color=bg_color)
            bg.paste(blend_image, mask=blend_image.getchannel(3))
            im = bg

        except (
            AttributeError,
            UnidentifiedImageError,
            TypeError,
        ) as e:
            if str(e) == "expected string or buffer":
                logger.info(
                    f"[ThumbRenderer][BLENDER][INFO] {filepath.name} "
                    f"Doesn't have an embedded thumbnail. ({type(e).__name__})"
                )

            else:
                logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
        return im

    @staticmethod
    def _source_engine(filepath: Path) -> Image.Image:
        """This is a function to convert the VTF (Valve Texture Format) files to thumbnails.

        It works using the VTF2IMG library for PILLOW.
        """
        parser = Parser(filepath)
        im: Image.Image = None
        try:
            im = parser.get_image()

        except (
            AttributeError,
            UnidentifiedImageError,
            TypeError,
            struct.error,
        ) as e:
            if str(e) == "expected string or buffer":
                logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)

            else:
                logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
        return im

    @staticmethod
    def _open_doc_thumb(filepath: Path) -> Image.Image:
        """Extract and render a thumbnail for an OpenDocument file.

        Args:
            filepath (Path): The path of the file.
        """
        file_path_within_zip = "Thumbnails/thumbnail.png"
        im: Image.Image = None
        with zipfile.ZipFile(filepath, "r") as zip_file:
            # Check if the file exists in the zip
            if file_path_within_zip in zip_file.namelist():
                # Read the specific file into memory
                file_data = zip_file.read(file_path_within_zip)
                thumb_im = Image.open(BytesIO(file_data))
                if thumb_im:
                    im = Image.new("RGB", thumb_im.size, color="#1e1e1e")
                    im.paste(thumb_im)
            else:
                logger.error("Couldn't render thumbnail", filepath=filepath)

        return im

    @staticmethod
    def _powerpoint_thumb(filepath: Path) -> Image.Image | None:
        """Extract and render a thumbnail for a Microsoft PowerPoint file.

        Args:
            filepath (Path): The path of the file.
        """
        file_path_within_zip = "docProps/thumbnail.jpeg"
        im: Image.Image | None = None
        try:
            with zipfile.ZipFile(filepath, "r") as zip_file:
                # Check if the file exists in the zip
                if file_path_within_zip in zip_file.namelist():
                    # Read the specific file into memory
                    file_data = zip_file.read(file_path_within_zip)
                    thumb_im = Image.open(BytesIO(file_data))
                    if thumb_im:
                        im = Image.new("RGB", thumb_im.size, color="#1e1e1e")
                        im.paste(thumb_im)
                else:
                    logger.error("Couldn't render thumbnail", filepath=filepath)
        except zipfile.BadZipFile as e:
            logger.error("Couldn't render thumbnail", filepath=filepath, error=e)

        return im

    @staticmethod
    def _epub_cover(filepath: Path) -> Image.Image:
        """Extracts and returns the first image found in the ePub file at the given filepath.

        Args:
            filepath (Path): The path to the ePub file.

        Returns:
            Image: The first image found in the ePub file, or None by default.
        """
        im: Image.Image = None
        try:
            with zipfile.ZipFile(filepath, "r") as zip_file:
                for file_name in zip_file.namelist():
                    if file_name.lower().endswith(
                        (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg")
                    ):
                        image_data = zip_file.read(file_name)
                        im = Image.open(BytesIO(image_data))
        except Exception as e:
            logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)

        return im

    def _font_short_thumb(self, filepath: Path, size: int) -> Image.Image:
        """Render a small font preview ("Aa") thumbnail from a font file.

        Args:
            filepath (Path): The path of the file.
            size (tuple[int,int]): The size of the thumbnail.
        """
        im: Image.Image = None
        try:
            bg = Image.new("RGB", (size, size), color="#000000")
            raw = Image.new("RGB", (size * 3, size * 3), color="#000000")
            draw = ImageDraw.Draw(raw)
            font = ImageFont.truetype(filepath, size=size)
            # NOTE: While a stroke effect is desired, the text
            # method only allows for outer strokes, which looks
            # a bit weird when rendering fonts.
            draw.text(
                (size // 8, size // 8),
                "Aa",
                font=font,
                fill="#FF0000",
                # stroke_width=math.ceil(size / 96),
                # stroke_fill="#FFFF00",
            )
            # NOTE: Change to getchannel(1) if using an outline.
            data = np.asarray(raw.getchannel(0))

            m, n = data.shape[:2]
            col: np.ndarray = data.any(0)
            row: np.ndarray = data.any(1)
            cropped_data = np.asarray(raw)[
                row.argmax() : m - row[::-1].argmax(),
                col.argmax() : n - col[::-1].argmax(),
            ]
            cropped_im: Image.Image = Image.fromarray(cropped_data, "RGB")

            margin: int = math.ceil(size // 16)

            orig_x, orig_y = cropped_im.size
            new_x, new_y = (size, size)
            if orig_x > orig_y:
                new_x = size
                new_y = math.ceil(size * (orig_y / orig_x))
            elif orig_y > orig_x:
                new_y = size
                new_x = math.ceil(size * (orig_x / orig_y))

            cropped_im = cropped_im.resize(
                size=(new_x - (margin * 2), new_y - (margin * 2)),
                resample=Image.Resampling.BILINEAR,
            )
            bg.paste(
                cropped_im,
                box=(margin, margin + ((size - new_y) // 2)),
            )
            im = self._apply_overlay_color(bg, UiColor.BLUE)
        except OSError as e:
            logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
        return im

    @staticmethod
    def _font_long_thumb(filepath: Path, size: int) -> Image.Image:
        """Render a large font preview ("Alphabet") thumbnail from a font file.

        Args:
            filepath (Path): The path of the file.
            size (tuple[int,int]): The size of the thumbnail.
        """
        # Scale the sample font sizes to the preview image
        # resolution,assuming the sizes are tuned for 256px.
        im: Image.Image = None
        try:
            scaled_sizes: list[int] = [math.floor(x * (size / 256)) for x in FONT_SAMPLE_SIZES]
            bg = Image.new("RGBA", (size, size), color="#00000000")
            draw = ImageDraw.Draw(bg)
            lines_of_padding = 2
            y_offset = 0

            for font_size in scaled_sizes:
                font = ImageFont.truetype(filepath, size=font_size)
                text_wrapped: str = wrap_full_text(
                    FONT_SAMPLE_TEXT, font=font, width=size, draw=draw
                )
                draw.multiline_text((0, y_offset), text_wrapped, font=font)
                y_offset += (len(text_wrapped.split("\n")) + lines_of_padding) * draw.textbbox(
                    (0, 0), "A", font=font
                )[-1]
            im = theme_fg_overlay(bg, use_alpha=False)
        except OSError as e:
            logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
        return im

    @staticmethod
    def _image_raw_thumb(filepath: Path) -> Image.Image:
        """Render a thumbnail for a RAW image type.

        Args:
            filepath (Path): The path of the file.
        """
        im: Image.Image = None
        try:
            with rawpy.imread(str(filepath)) as raw:
                rgb = raw.postprocess(use_camera_wb=True)
                im = Image.frombytes(
                    "RGB",
                    (rgb.shape[1], rgb.shape[0]),
                    rgb,
                    decoder_name="raw",
                )
        except (
            DecompressionBombError,
            rawpy._rawpy.LibRawIOError,
            rawpy._rawpy.LibRawFileUnsupportedError,
        ) as e:
            logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
        return im

    @staticmethod
    def _image_thumb(filepath: Path) -> Image.Image:
        """Render a thumbnail for a standard image type.

        Args:
            filepath (Path): The path of the file.
        """
        im: Image.Image = None
        try:
            im = Image.open(filepath)
            if im.mode != "RGB" and im.mode != "RGBA":
                im = im.convert(mode="RGBA")
            if im.mode == "RGBA":
                new_bg = Image.new("RGB", im.size, color="#1e1e1e")
                new_bg.paste(im, mask=im.getchannel(3))
                im = new_bg
            im = ImageOps.exif_transpose(im)
        except (
            UnidentifiedImageError,
            DecompressionBombError,
            NotImplementedError,
        ) as e:
            logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
        return im

    @staticmethod
    def _image_vector_thumb(filepath: Path, size: int) -> Image.Image:
        """Render a thumbnail for a vector image, such as SVG.

        Args:
            filepath (Path): The path of the file.
            size (tuple[int,int]): The size of the thumbnail.
        """
        im: Image.Image = None
        # Create an image to draw the svg to and a painter to do the drawing
        q_image: QImage = QImage(size, size, QImage.Format.Format_ARGB32)
        q_image.fill("#1e1e1e")

        # Create an svg renderer, then render to the painter
        svg: QSvgRenderer = QSvgRenderer(str(filepath))

        if not svg.isValid():
            raise UnidentifiedImageError

        painter: QPainter = QPainter(q_image)
        svg.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        svg.render(painter)
        painter.end()

        # Write the image to a buffer as png
        buffer: QBuffer = QBuffer()
        buffer.open(QBuffer.OpenModeFlag.ReadWrite)
        q_image.save(buffer, "PNG")  # type: ignore[call-overload]

        # Load the image from the buffer
        im = Image.new("RGB", (size, size), color="#1e1e1e")
        im.paste(Image.open(BytesIO(buffer.data().data())))
        im = im.convert(mode="RGB")

        buffer.close()
        return im

    @staticmethod
    def _iwork_thumb(filepath: Path) -> Image.Image:
        """Extract and render a thumbnail for an Apple iWork (Pages, Numbers, Keynote) file.

        Args:
            filepath (Path): The path of the file.
        """
        preview_thumb_dir = "preview.jpg"
        quicklook_thumb_dir = "QuickLook/Thumbnail.jpg"
        im: Image.Image | None = None

        def get_image(path: str) -> Image.Image | None:
            thumb_im: Image.Image | None = None
            # Read the specific file into memory
            file_data = zip_file.read(path)
            thumb_im = Image.open(BytesIO(file_data))
            return thumb_im

        try:
            with zipfile.ZipFile(filepath, "r") as zip_file:
                thumb: Image.Image | None = None

                # Check if the file exists in the zip
                if preview_thumb_dir in zip_file.namelist():
                    thumb = get_image(preview_thumb_dir)
                elif quicklook_thumb_dir in zip_file.namelist():
                    thumb = get_image(quicklook_thumb_dir)
                else:
                    logger.error("Couldn't render thumbnail", filepath=filepath)

                if thumb:
                    im = Image.new("RGB", thumb.size, color="#1e1e1e")
                    im.paste(thumb)
        except zipfile.BadZipFile as e:
            logger.error("Couldn't render thumbnail", filepath=filepath, error=e)

        return im

    @staticmethod
    def _model_stl_thumb(filepath: Path, size: int) -> Image.Image:
        """Render a thumbnail for an STL file.

        Args:
            filepath (Path): The path of the file.
            size (tuple[int,int]): The size of the icon.
        """
        # TODO: Implement.
        # The following commented code describes a method for rendering via
        # matplotlib.
        # This implementation did not play nice with multithreading.
        im: Image.Image = None
        # # Create a new plot
        # matplotlib.use('agg')
        # figure = plt.figure()
        # axes = figure.add_subplot(projection='3d')

        # # Load the STL files and add the vectors to the plot
        # your_mesh = mesh.Mesh.from_file(_filepath)

        # poly_collection = mplot3d.art3d.Poly3DCollection(your_mesh.vectors)
        # poly_collection.set_color((0,0,1))  # play with color
        # scale = your_mesh.points.flatten()
        # axes.auto_scale_xyz(scale, scale, scale)
        # axes.add_collection3d(poly_collection)
        # # plt.show()
        # img_buf = io.BytesIO()
        # plt.savefig(img_buf, format='png')
        # im = Image.open(img_buf)

        return im

    @staticmethod
    def _pdf_thumb(filepath: Path, size: int) -> Image.Image:
        """Render a thumbnail for a PDF file.

        filepath (Path): The path of the file.
            size (int): The size of the icon.
        """
        im: Image.Image = None

        file: QFile = QFile(filepath)
        success: bool = file.open(
            QIODeviceBase.OpenModeFlag.ReadOnly, QFileDevice.Permission.ReadUser
        )
        if not success:
            logger.error("Couldn't render thumbnail", filepath=filepath)
            return im
        document: QPdfDocument = QPdfDocument()
        document.load(file)
        file.close()
        # Transform page_size in points to pixels with proper aspect ratio
        page_size: QSizeF = document.pagePointSize(0)
        ratio_hw: float = page_size.height() / page_size.width()
        if ratio_hw >= 1:
            page_size *= size / page_size.height()
        else:
            page_size *= size / page_size.width()
        # Enlarge image for antialiasing
        scale_factor = 2.5
        page_size *= scale_factor
        # Render image with no anti-aliasing for speed
        render_options: QPdfDocumentRenderOptions = QPdfDocumentRenderOptions()
        render_options.setRenderFlags(
            QPdfDocumentRenderOptions.RenderFlag.TextAliased
            | QPdfDocumentRenderOptions.RenderFlag.ImageAliased
            | QPdfDocumentRenderOptions.RenderFlag.PathAliased
        )
        # Convert QImage to PIL Image
        q_image: QImage = document.render(0, page_size.toSize(), render_options)
        buffer: QBuffer = QBuffer()
        buffer.open(QBuffer.OpenModeFlag.ReadWrite)
        try:
            q_image.save(buffer, "PNG")  # type: ignore # pyright: ignore
            im = Image.open(BytesIO(buffer.buffer().data()))
        finally:
            buffer.close()
        # Replace transparent pixels with white (otherwise Background defaults to transparent)
        return replace_transparent_pixels(im)

    @staticmethod
    def _text_thumb(filepath: Path) -> Image.Image | None:
        """Render a thumbnail for a plaintext file.

        Args:
            filepath (Path): The path of the file.
        """
        im: Image.Image | None = None

        bg_color: str = (
            "#1e1e1e"
            if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
            else "#FFFFFF"
        )
        fg_color: str = (
            "#FFFFFF"
            if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
            else "#111111"
        )

        try:
            encoding = detect_char_encoding(filepath)
            with open(filepath, encoding=encoding) as text_file:
                text = text_file.read(256)
            bg = Image.new("RGB", (256, 256), color=bg_color)
            draw = ImageDraw.Draw(bg)
            draw.text((16, 16), text, fill=fg_color)
            im = bg
        except (
            UnidentifiedImageError,
            cv2.error,
            DecompressionBombError,
            UnicodeDecodeError,
            OSError,
        ) as e:
            logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
        return im

    @staticmethod
    def _video_thumb(filepath: Path) -> Image.Image | None:
        """Render a thumbnail for a video file.

        Args:
            filepath (Path): The path of the file.
        """
        im: Image.Image | None = None
        frame: MatLike | None = None
        try:
            if is_readable_video(filepath):
                video = cv2.VideoCapture(str(filepath), cv2.CAP_FFMPEG)
                # TODO: Move this check to is_readable_video()
                if video.get(cv2.CAP_PROP_FRAME_COUNT) <= 0:
                    raise cv2.error("File is invalid or has 0 frames")
                video.set(
                    cv2.CAP_PROP_POS_FRAMES,
                    (video.get(cv2.CAP_PROP_FRAME_COUNT) // 2),
                )
                # NOTE: Depending on the video format, compression, and
                # frame count, seeking halfway does not work and the thumb
                # must be pulled from the earliest available frame.
                max_frame_seek: int = 10
                for i in range(
                    0,
                    min(max_frame_seek, math.floor(video.get(cv2.CAP_PROP_FRAME_COUNT))),
                ):
                    success, frame = video.read()
                    if not success:
                        video.set(cv2.CAP_PROP_POS_FRAMES, i)
                    else:
                        break
                if frame is not None:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    im = Image.fromarray(frame)
        except (
            UnidentifiedImageError,
            cv2.error,
            DecompressionBombError,
            OSError,
        ) as e:
            logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
        return im

    def render(
        self,
        timestamp: float,
        filepath: Path | str,
        base_size: tuple[int, int],
        pixel_ratio: float,
        is_loading: bool = False,
        is_grid_thumb: bool = False,
        update_on_ratio_change: bool = False,
    ):
        """Render a thumbnail or preview image.

        Args:
            timestamp (float): The timestamp for which this this job was dispatched.
            filepath (str | Path): The path of the file to render a thumbnail for.
            base_size (tuple[int,int]): The unmodified base size of the thumbnail.
            pixel_ratio (float): The screen pixel ratio.
            is_loading (bool): Is this a loading graphic?
            is_grid_thumb (bool): Is this a thumbnail for the thumbnail grid?
                Or else the Preview Pane?
            update_on_ratio_change (bool): Should an updated ratio signal be sent?
        """
        render_mask_and_edge: bool = True
        adj_size = math.ceil(max(base_size[0], base_size[1]) * pixel_ratio)
        theme_color: UiColor = (
            UiColor.THEME_LIGHT
            if QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Light
            else UiColor.THEME_DARK
        )
        if isinstance(filepath, str):
            filepath = Path(filepath)

        def render_default(size: tuple[int, int], pixel_ratio: float) -> Image.Image:
            im = self._get_icon(
                name=self._get_resource_id(filepath),
                color=theme_color,
                size=size,
                pixel_ratio=pixel_ratio,
            )
            return im

        def render_unlinked(size: tuple[int, int], pixel_ratio: float) -> Image.Image:
            im = self._get_icon(
                name="broken_link_icon",
                color=UiColor.RED,
                size=size,
                pixel_ratio=pixel_ratio,
            )
            return im

        def fetch_cached_image(folder: Path):
            image: Image.Image | None = None
            cached_path: Path | None = None

            if hash_value and self.lib.library_dir:
                cached_path = Path(
                    self.lib.library_dir
                    / TS_FOLDER_NAME
                    / THUMB_CACHE_NAME
                    / folder
                    / f"{hash_value}{ThumbRenderer.cached_img_ext}"
                )
            if cached_path and cached_path.exists() and not cached_path.is_dir():
                try:
                    image = Image.open(cached_path)
                    if not image:
                        raise UnidentifiedImageError  # pyright: ignore[reportUnreachable]
                    ThumbRenderer.last_cache_folder = folder
                except Exception as e:
                    logger.error(
                        "[ThumbRenderer] Couldn't open cached thumbnail!",
                        path=cached_path,
                        error=e,
                    )
                    # If the cached thumbnail failed, try rendering a new one
                    image = self._render(
                        timestamp,
                        filepath,
                        (ThumbRenderer.cached_img_res, ThumbRenderer.cached_img_res),
                        1,
                        is_grid_thumb,
                        save_to_file=cached_path,
                    )

            return image

        image: Image.Image | None = None
        # Try to get a non-loading thumbnail for the grid.
        if not is_loading and is_grid_thumb and filepath and filepath != Path("."):
            # Attempt to retrieve cached image from disk
            mod_time: str = ""
            with contextlib.suppress(Exception):
                mod_time = str(filepath.stat().st_mtime_ns)
            hashable_str: str = f"{str(filepath)}{mod_time}"
            hash_value = hashlib.shake_128(hashable_str.encode("utf-8")).hexdigest(8)

            # Check the last successful folder first.
            if ThumbRenderer.last_cache_folder:
                image = fetch_cached_image(ThumbRenderer.last_cache_folder)

            # If there was no last folder or the check failed, check all folders.
            if not image:
                thumb_folders: list[Path] = []
                try:
                    for f in (self.lib.library_dir / TS_FOLDER_NAME / THUMB_CACHE_NAME).glob("*"):
                        if f.is_dir() and f is not ThumbRenderer.last_cache_folder:
                            thumb_folders.append(f)
                except TypeError:
                    logger.error(
                        "[ThumbRenderer] Couldn't check thumb cache folder, is the library closed?",
                        library_dir=self.lib.library_dir,
                    )

                for folder in thumb_folders:
                    image = fetch_cached_image(folder)
                    if image:
                        ThumbRenderer.last_cache_folder = folder
                        break
            if not image:
                # Render from file, return result, and try to save a cached version.
                # TODO: Audio waveforms are dynamically sized based on the base_size, so hardcoding
                # the resolution breaks that.
                image = self._render(
                    timestamp,
                    filepath,
                    (ThumbRenderer.cached_img_res, ThumbRenderer.cached_img_res),
                    1,
                    is_grid_thumb,
                    save_to_file=Path(f"{hash_value}{ThumbRenderer.cached_img_ext}"),
                )
                # If the normal renderer failed, fallback the the defaults
                # (with native non-cached sizing!)
                if not image:
                    image = (
                        render_unlinked((adj_size, adj_size), pixel_ratio)
                        if not filepath.exists()
                        else render_default((adj_size, adj_size), pixel_ratio)
                    )
                    render_mask_and_edge = False

            # Apply the mask and edge
            if image:
                image = self._resize_image(image, (adj_size, adj_size))
                if render_mask_and_edge:
                    mask = self._get_mask((adj_size, adj_size), pixel_ratio)
                    edge: tuple[Image.Image, Image.Image] = self._get_edge(
                        (adj_size, adj_size), pixel_ratio
                    )
                    image = self._apply_edge(
                        four_corner_gradient(image, (adj_size, adj_size), mask), edge
                    )

        # A loading thumbnail (cached in memory)
        elif is_loading:
            # Initialize "Loading" thumbnail
            loading_thumb: Image.Image = self._get_icon(
                "thumb_loading", theme_color, (adj_size, adj_size), pixel_ratio
            )
            image = loading_thumb.resize((adj_size, adj_size), resample=Image.Resampling.BILINEAR)

        # A full preview image (never cached)
        elif not is_grid_thumb:
            image = self._render(timestamp, filepath, base_size, pixel_ratio)
            if not image:
                image = (
                    render_unlinked((512, 512), 2)
                    if not filepath.exists()
                    else render_default((512, 512), 2)
                )
                render_mask_and_edge = False
            mask = self._get_mask(image.size, pixel_ratio, scale_radius=True)
            bg = Image.new("RGBA", image.size, (0, 0, 0, 0))
            bg.paste(image, mask=mask.getchannel(0))
            image = bg

        # If the image couldn't be rendered, use a default media image.
        if not image:
            image = Image.new("RGBA", (128, 128), color="#FF00FF")

        # Convert the final image to a pixmap to emit.
        qim = ImageQt.ImageQt(image)
        pixmap = QPixmap.fromImage(qim)
        pixmap.setDevicePixelRatio(pixel_ratio)
        self.updated_ratio.emit(image.size[0] / image.size[1])
        if pixmap:
            self.updated.emit(
                timestamp,
                pixmap,
                QSize(
                    math.ceil(adj_size / pixel_ratio),
                    math.ceil(image.size[1] / pixel_ratio),
                ),
                filepath,
                filepath.suffix.lower(),
            )
        else:
            self.updated.emit(
                timestamp,
                QPixmap(),
                QSize(*base_size),
                filepath,
                filepath.suffix.lower(),
            )

    def _render(
        self,
        timestamp: float,
        filepath: str | Path,
        base_size: tuple[int, int],
        pixel_ratio: float,
        is_grid_thumb: bool = False,
        save_to_file: Path | None = None,
    ) -> Image.Image | None:
        """Render a thumbnail or preview image.

        Args:
            timestamp (float): The timestamp for which this this job was dispatched.
            filepath (str | Path): The path of the file to render a thumbnail for.
            base_size (tuple[int,int]): The unmodified base size of the thumbnail.
            pixel_ratio (float): The screen pixel ratio.
            is_grid_thumb (bool): Is this a thumbnail for the thumbnail grid?
                Or else the Preview Pane?
            save_to_file(Path | None): A filepath to optionally save the output to.

        """
        adj_size = math.ceil(max(base_size[0], base_size[1]) * pixel_ratio)
        image: Image.Image | None = None
        _filepath: Path = Path(filepath)
        savable_media_type: bool = True

        if _filepath:
            try:
                # Missing Files ================================================
                if not _filepath.exists():
                    raise FileNotFoundError
                ext: str = _filepath.suffix.lower() if _filepath.suffix else _filepath.stem.lower()
                # Images =======================================================
                if MediaCategories.is_ext_in_category(
                    ext, MediaCategories.IMAGE_TYPES, mime_fallback=True
                ):
                    # Raw Images -----------------------------------------------
                    if MediaCategories.is_ext_in_category(
                        ext, MediaCategories.IMAGE_RAW_TYPES, mime_fallback=True
                    ):
                        image = self._image_raw_thumb(_filepath)
                    # Vector Images --------------------------------------------
                    elif MediaCategories.is_ext_in_category(
                        ext, MediaCategories.IMAGE_VECTOR_TYPES, mime_fallback=True
                    ):
                        image = self._image_vector_thumb(_filepath, adj_size)
                    # Normal Images --------------------------------------------
                    else:
                        image = self._image_thumb(_filepath)
                # Videos =======================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.VIDEO_TYPES, mime_fallback=True
                ):
                    image = self._video_thumb(_filepath)
                # PowerPoint Slideshow
                elif ext in {".pptx"}:
                    image = self._powerpoint_thumb(_filepath)
                # OpenDocument/OpenOffice ======================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.OPEN_DOCUMENT_TYPES, mime_fallback=True
                ):
                    image = self._open_doc_thumb(_filepath)
                # Apple iWork Suite ============================================
                elif MediaCategories.is_ext_in_category(ext, MediaCategories.IWORK_TYPES):
                    image = self._iwork_thumb(_filepath)
                # Plain Text ===================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.PLAINTEXT_TYPES, mime_fallback=True
                ):
                    image = self._text_thumb(_filepath)
                # Fonts ========================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.FONT_TYPES, mime_fallback=True
                ):
                    if is_grid_thumb:
                        # Short (Aa) Preview
                        image = self._font_short_thumb(_filepath, adj_size)
                    else:
                        # Large (Full Alphabet) Preview
                        image = self._font_long_thumb(_filepath, adj_size)
                # Audio ========================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.AUDIO_TYPES, mime_fallback=True
                ):
                    image = self._audio_album_thumb(_filepath, ext)
                    if image is None:
                        image = self._audio_waveform_thumb(_filepath, ext, adj_size, pixel_ratio)
                        savable_media_type = False
                        if image is not None:
                            image = self._apply_overlay_color(image, UiColor.GREEN)
                # Ebooks =======================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.EBOOK_TYPES, mime_fallback=True
                ):
                    image = self._epub_cover(_filepath)
                # Blender ======================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.BLENDER_TYPES, mime_fallback=True
                ):
                    image = self._blender(_filepath)
                # PDF ==========================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.PDF_TYPES, mime_fallback=True
                ):
                    image = self._pdf_thumb(_filepath, adj_size)
                # VTF ==========================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.SOURCE_ENGINE_TYPES, mime_fallback=True
                ):
                    image = self._source_engine(_filepath)
                # No Rendered Thumbnail ========================================
                if not image:
                    raise NoRendererError

                if image:
                    image = self._resize_image(image, (adj_size, adj_size))

                if save_to_file and savable_media_type and image:
                    ThumbRenderer.cache.save_image(image, save_to_file, mode="RGBA")

            except FileNotFoundError:
                image = None
            except (
                UnidentifiedImageError,
                DecompressionBombError,
                ValueError,
                ChildProcessError,
            ) as e:
                logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
                image = None
            except NoRendererError:
                image = None

        return image

    def _resize_image(self, image: Image.Image, size: tuple[int, int]) -> Image.Image:
        orig_x, orig_y = image.size
        new_x, new_y = size

        if orig_x > orig_y:
            new_x = size[0]
            new_y = math.ceil(size[1] * (orig_y / orig_x))
        elif orig_y > orig_x:
            new_y = size[1]
            new_x = math.ceil(size[0] * (orig_x / orig_y))

        resampling_method = (
            Image.Resampling.NEAREST
            if max(image.size[0], image.size[1]) < max(size)
            else Image.Resampling.BILINEAR
        )
        image = image.resize((new_x, new_y), resample=resampling_method)

        return image
