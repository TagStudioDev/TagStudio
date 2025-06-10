# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import math
import os
import struct
import zipfile
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from io import BytesIO
from pathlib import Path
from typing import cast
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
    UnidentifiedImageError,
)
from PIL.Image import DecompressionBombError
from pillow_heif import register_avif_opener, register_heif_opener
from PySide6.QtCore import (
    QBuffer,
    QFile,
    QFileDevice,
    QIODeviceBase,
    QSizeF,
    Qt,
)
from PySide6.QtGui import QImage, QPainter
from PySide6.QtPdf import QPdfDocument, QPdfDocumentRenderOptions
from PySide6.QtSvg import QSvgRenderer
from vtf2img import Parser

from tagstudio.core.constants import (
    FONT_SAMPLE_SIZES,
    FONT_SAMPLE_TEXT,
)
from tagstudio.core.exceptions import NoRendererError
from tagstudio.core.media_types import MediaCategories, MediaType
from tagstudio.core.palette import ColorType, UiColor, get_ui_color
from tagstudio.core.utils.encoding import detect_char_encoding
from tagstudio.qt import cache_manager
from tagstudio.qt.helpers.blender_thumbnailer import blend_thumb
from tagstudio.qt.helpers.color_overlay import theme_fg_overlay
from tagstudio.qt.helpers.file_tester import is_readable_video
from tagstudio.qt.helpers.gradient import four_corner_gradient
from tagstudio.qt.helpers.image_effects import replace_transparent_pixels
from tagstudio.qt.helpers.text_wrapper import wrap_full_text
from tagstudio.qt.helpers.vendored.pydub.audio_segment import (
    _AudioSegment as AudioSegment,
)

ImageFile.LOAD_TRUNCATED_IMAGES = True

logger = structlog.get_logger(__name__)
Image.MAX_IMAGE_PIXELS = None
register_heif_opener()
register_avif_opener()

try:
    import pillow_jxl  # noqa: F401 # pyright: ignore[reportUnusedImport]
except ImportError:
    logger.exception('[ThumbRenderer] Could not import the "pillow_jxl" module')


def _dummy():
    pass


def init_worker():
    import os

    os.setpriority(os.PRIO_PROCESS, 0, 10)


def init_pool() -> ProcessPoolExecutor:
    import multiprocessing

    context = multiprocessing.get_context(method="spawn")
    max_workers = int((os.cpu_count() or 2) / 2)
    pool = ProcessPoolExecutor(max_workers=max_workers, mp_context=context, initializer=init_worker)
    for _ in range(max_workers):
        pool.submit(_dummy)
    return pool


def _render_thumbnail(
    file_path: Path,
    base_size: tuple[int, int],
    pixel_ratio: float,
    is_dark_theme: bool,
    cache_folder: Path,
) -> Image.Image | None:
    """Render a thumbnail image.

    Args:
        file_path (Path): The path of the file to render a thumbnail for.
        base_size (tuple[int,int]): The unmodified base size of the thumbnail.
        pixel_ratio (float): The screen pixel ratio.
        is_dark_theme (bool): Determines what background colors should be used.
        cache_folder (Path): The path to look for and save cached thumbnails.
    """
    adj_size = math.ceil(max(base_size[0], base_size[1]) * pixel_ratio)

    image: Image.Image | None = None
    cache_path = cache_manager.get_cache_path(cache_folder, file_path)
    if cache_path.exists():
        image = Image.open(cache_path)
    else:
        # TODO: Audio waveforms are dynamically sized based on the base_size, so hardcoding
        # the resolution breaks that.
        is_preview = False
        image = _render(
            file_path, (256, 256), 1.0, is_preview, is_dark_theme, cache_folder=cache_folder
        )

    if image is None:
        return None

    # Apply the mask and edge
    image = _resize_image(image, (adj_size, adj_size))
    mask = _render_mask((adj_size, adj_size), pixel_ratio, radius_scale=1.0)
    edge = _render_edge((adj_size, adj_size), pixel_ratio)
    image = _apply_edge(
        four_corner_gradient(image, (adj_size, adj_size), mask),
        edge,
        shade_reduction=0.0 if is_dark_theme else 0.3,
    )

    return image


def _render_preview(
    file_path: Path,
    base_size: tuple[int, int],
    pixel_ratio: float,
    is_dark_theme: bool,
) -> Image.Image | None:
    """Render a preview image.

    Args:
        file_path (Path): The path of the file to render a thumbnail for.
        base_size (tuple[int,int]): The unmodified base size of the thumbnail.
        pixel_ratio (float): The screen pixel ratio.
        is_dark_theme (bool): Determines what background colors should be used.
    """
    is_preview = True
    image = _render(file_path, base_size, pixel_ratio, is_preview, is_dark_theme)
    if image is None:
        return None

    mask = _render_mask(image.size, pixel_ratio, radius_scale=1)
    bg = Image.new("RGBA", image.size, (0, 0, 0, 0))
    bg.paste(image, mask=mask.getchannel(0))
    return bg


def _render_icon(
    file_path: Path,
    color: UiColor,
    size: tuple[int, int],
    pixel_ratio: float,
    draw_border: bool,
    is_dark_theme: bool,
) -> Image.Image | None:
    """Render a thumbnail icon.

    Args:
        file_path (Path): The path of the file to render a thumbnail for.
        color (UiColor): The color to use for the icon.
        size (tuple[int,int]): The size of the icon.
        pixel_ratio (float): The screen pixel ratio.
        draw_border (bool): Option to draw a border.
        is_dark_theme (bool): Determines what background colors should be used.
    """
    icon: Image.Image = Image.open(file_path)
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
    smoothed_size = size[0] * smooth_factor, size[1] * smooth_factor
    im.paste(
        bg,
        (0, 0),
        mask=_render_mask(smoothed_size, pixel_ratio * smooth_factor),
    )

    # Draw rounded rectangle border
    if draw_border:
        draw = ImageDraw.Draw(im)
        draw.rounded_rectangle(
            (0, 0) + tuple([d - 1 for d in im.size]),
            radius=math.ceil((radius_factor * smooth_factor * pixel_ratio) + (pixel_ratio * 1.5)),
            fill="black",
            outline="#FF0000",
            width=math.floor((border_factor * smooth_factor * pixel_ratio) - (pixel_ratio * 1.5)),
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
    im = _apply_overlay_color(im, color, is_dark_theme)

    edge = _render_edge(size, pixel_ratio)
    im = _apply_edge(im, edge, faded=True, shade_reduction=0.0 if is_dark_theme else 0.3)

    return im


def _render(
    file_path: Path,
    base_size: tuple[int, int],
    pixel_ratio: float,
    is_preview: bool,
    is_dark_theme: bool,
    cache_folder: Path | None = None,
) -> Image.Image | None:
    # Missing Files ================================================
    if not file_path.exists():
        raise FileNotFoundError
    adj_size = math.ceil(max(base_size[0], base_size[1]) * pixel_ratio)
    image = None
    savable_media_type: bool = True

    try:
        ext: str = file_path.suffix.lower() if file_path.suffix else file_path.stem.lower()
        # Images =======================================================
        if MediaCategories.is_ext_in_category(ext, MediaCategories.IMAGE_TYPES, mime_fallback=True):
            # Raw Images -----------------------------------------------
            if MediaCategories.is_ext_in_category(
                ext, MediaCategories.IMAGE_RAW_TYPES, mime_fallback=True
            ):
                image = _image_raw_thumb(file_path)
            # Vector Images --------------------------------------------
            elif MediaCategories.is_ext_in_category(
                ext, MediaCategories.IMAGE_VECTOR_TYPES, mime_fallback=True
            ):
                image = _image_vector_thumb(file_path, adj_size)
            # Normal Images --------------------------------------------
            else:
                image = _image_thumb(file_path)
        # Videos =======================================================
        elif MediaCategories.is_ext_in_category(
            ext, MediaCategories.VIDEO_TYPES, mime_fallback=True
        ):
            image = _video_thumb(file_path)
        # PowerPoint Slideshow
        elif ext in {".pptx"}:
            image = _powerpoint_thumb(file_path)
        # OpenDocument/OpenOffice ======================================
        elif MediaCategories.is_ext_in_category(
            ext, MediaCategories.OPEN_DOCUMENT_TYPES, mime_fallback=True
        ):
            image = _open_doc_thumb(file_path)
        # Apple iWork Suite ============================================
        elif MediaCategories.is_ext_in_category(ext, MediaCategories.IWORK_TYPES):
            image = _iwork_thumb(file_path)
        # Plain Text ===================================================
        elif MediaCategories.is_ext_in_category(
            ext, MediaCategories.PLAINTEXT_TYPES, mime_fallback=True
        ):
            image = _text_thumb(file_path)
        # Fonts ========================================================
        elif MediaCategories.is_ext_in_category(
            ext, MediaCategories.FONT_TYPES, mime_fallback=True
        ):
            if is_preview:
                # Large (Full Alphabet) Preview
                image = _font_long_thumb(file_path, adj_size)
            else:
                # Short (Aa) Preview
                image = _font_short_thumb(file_path, adj_size, is_dark_theme)
        # Audio ========================================================
        elif MediaCategories.is_ext_in_category(
            ext, MediaCategories.AUDIO_TYPES, mime_fallback=True
        ):
            image = _audio_album_thumb(file_path, ext)
            if image is None:
                image = _audio_waveform_thumb(file_path, ext, adj_size, pixel_ratio)
                savable_media_type = False
                if image is not None:
                    image = _apply_overlay_color(image, UiColor.GREEN, is_dark_theme)
        # Ebooks =======================================================
        elif MediaCategories.is_ext_in_category(
            ext, MediaCategories.EBOOK_TYPES, mime_fallback=True
        ):
            image = _epub_cover(file_path)
        # Blender ======================================================
        elif MediaCategories.is_ext_in_category(
            ext, MediaCategories.BLENDER_TYPES, mime_fallback=True
        ):
            image = _blender(file_path)
        # PDF ==========================================================
        elif MediaCategories.is_ext_in_category(ext, MediaCategories.PDF_TYPES, mime_fallback=True):
            image = _pdf_thumb(file_path, adj_size)
        # VTF ==========================================================
        elif MediaCategories.is_ext_in_category(
            ext, MediaCategories.SOURCE_ENGINE_TYPES, mime_fallback=True
        ):
            image = _source_engine(file_path)
        # No Rendered Thumbnail ========================================
        if not image:
            raise NoRendererError

        if image:
            image = _resize_image(image, (adj_size, adj_size))

            if cache_folder is not None and savable_media_type:
                cache_path = cache_manager.get_cache_path(cache_folder, file_path)
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                image.save(cache_path, mode="RGBA")

    except (
        UnidentifiedImageError,
        DecompressionBombError,
        ValueError,
        ChildProcessError,
    ) as e:
        logger.error(
            "[ThumbnailManager] Couldn't render thumbnail",
            filepath=file_path,
            error_name=type(e).__name__,
            error=e,
        )
        image = None
    except NoRendererError:
        image = None

    return image


def _render_mask(size: tuple[int, int], pixel_ratio: float, radius_scale: float = 1) -> Image.Image:
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


def _render_edge(size: tuple[int, int], pixel_ratio: float) -> tuple[Image.Image, Image.Image]:
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


def _apply_edge(
    image: Image.Image,
    edge: tuple[Image.Image, Image.Image],
    faded: bool = False,
    shade_reduction: float = 0.3,
) -> Image.Image:
    """Apply a given edge effect to an image.

    Args:
        image (Image.Image): The image to apply the edge to.
        edge (tuple[Image.Image, Image.Image]): The edge images to apply.
            Item 0 is the inner highlight, and item 1 is the outer shadow.
        faded (bool): Whether or not to apply a faded version of the edge.
            Used for light themes.
        shade_reduction (float): TODO
    """
    opacity: float = 1.0 if not faded else 0.8
    # shade_reduction: float = (
    #    0 if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark else 0.3
    # )
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


def _apply_overlay_color(image: Image.Image, color: UiColor, is_dark_theme: bool) -> Image.Image:
    """Apply a color overlay effect to an image based on its color channel data.

    Red channel for foreground, green channel for outline, none for background.

    Args:
        image (Image.Image): The image to apply an overlay to.
        color (UiColor): The name of the ColorType color to use.
        is_dark_theme (bool): Determines what background colors should be used.
    """
    bg_color: str = (
        get_ui_color(ColorType.DARK_ACCENT, color)
        if is_dark_theme
        else get_ui_color(ColorType.PRIMARY, color)
    )
    fg_color: str = (
        get_ui_color(ColorType.PRIMARY, color)
        if is_dark_theme
        else get_ui_color(ColorType.LIGHT_ACCENT, color)
    )
    ol_color: str = (
        get_ui_color(ColorType.BORDER, color)
        if is_dark_theme
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
    im: Image.Image | None = None

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


def _blender(filepath: Path, is_dark_theme: bool) -> Image.Image | None:
    """Get an emended thumbnail from a Blender file, if a thumbnail is present.

    Args:
        filepath (Path): The path of the file.
    """
    bg_color: str = "#1e1e1e" if is_dark_theme else "#FFFFFF"
    im: Image.Image | None = None
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


def _source_engine(filepath: Path) -> Image.Image | None:
    """This is a function to convert the VTF (Valve Texture Format) files to thumbnails.

    It works using the VTF2IMG library for PILLOW.
    """
    parser = Parser(str(filepath))
    im: Image.Image | None = None
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


def _open_doc_thumb(filepath: Path) -> Image.Image | None:
    """Extract and render a thumbnail for an OpenDocument file.

    Args:
        filepath (Path): The path of the file.
    """
    file_path_within_zip = "Thumbnails/thumbnail.png"
    im: Image.Image | None = None
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


def _epub_cover(filepath: Path) -> Image.Image | None:
    """Extracts and returns the first image found in the ePub file at the given filepath.

    Args:
        filepath (Path): The path to the ePub file.

    Returns:
        Image: The first image found in the ePub file, or None by default.
    """
    im: Image.Image | None = None
    try:
        with zipfile.ZipFile(filepath, "r") as zip_file:
            for file_name in zip_file.namelist():
                if file_name.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg")):
                    image_data = zip_file.read(file_name)
                    im = Image.open(BytesIO(image_data))
    except Exception as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)

    return im


def _font_short_thumb(filepath: Path, size: int, is_dark_theme: bool) -> Image.Image | None:
    """Render a small font preview ("Aa") thumbnail from a font file.

    Args:
        filepath (Path): The path of the file.
        size (tuple[int,int]): The size of the thumbnail.
        is_dark_theme (bool): Determines what background colors should be used.
    """
    im: Image.Image | None = None
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
        col: np.ndarray = cast(np.ndarray, data.any(0))
        row: np.ndarray = cast(np.ndarray, data.any(1))
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
        im = _apply_overlay_color(bg, UiColor.BLUE, is_dark_theme)
    except OSError as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
    return im


def _font_long_thumb(filepath: Path, size: int) -> Image.Image | None:
    """Render a large font preview ("Alphabet") thumbnail from a font file.

    Args:
        filepath (Path): The path of the file.
        size (tuple[int,int]): The size of the thumbnail.
    """
    # Scale the sample font sizes to the preview image
    # resolution,assuming the sizes are tuned for 256px.
    im: Image.Image | None = None
    try:
        scaled_sizes: list[int] = [math.floor(x * (size / 256)) for x in FONT_SAMPLE_SIZES]
        bg = Image.new("RGBA", (size, size), color="#00000000")
        draw = ImageDraw.Draw(bg)
        lines_of_padding = 2
        y_offset = 0.0

        for font_size in scaled_sizes:
            font = ImageFont.truetype(filepath, size=font_size)
            text_wrapped: str = wrap_full_text(FONT_SAMPLE_TEXT, font=font, width=size, draw=draw)
            draw.multiline_text((0, y_offset), text_wrapped, font=font)
            y_offset += (len(text_wrapped.split("\n")) + lines_of_padding) * draw.textbbox(
                (0, 0), "A", font=font
            )[-1]
        im = theme_fg_overlay(bg, use_alpha=False)
    except OSError as e:
        logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
    return im


def _image_raw_thumb(filepath: Path) -> Image.Image | None:
    """Render a thumbnail for a RAW image type.

    Args:
        filepath (Path): The path of the file.
    """
    im: Image.Image | None = None
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


def _image_thumb(filepath: Path) -> Image.Image | None:
    """Render a thumbnail for a standard image type.

    Args:
        filepath (Path): The path of the file.
    """
    im: Image.Image | None = None
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


def _image_vector_thumb(filepath: Path, size: int) -> Image.Image | None:
    """Render a thumbnail for a vector image, such as SVG.

    Args:
        filepath (Path): The path of the file.
        size (tuple[int,int]): The size of the thumbnail.
    """
    im: Image.Image | None = None
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


def _iwork_thumb(filepath: Path) -> Image.Image | None:
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


def _model_stl_thumb(filepath: Path, size: int) -> Image.Image | None:
    """Render a thumbnail for an STL file.

    Args:
        filepath (Path): The path of the file.
        size (tuple[int,int]): The size of the icon.
    """
    # TODO: Implement.
    # The following commented code describes a method for rendering via
    # matplotlib.
    # This implementation did not play nice with multithreading.
    im: Image.Image | None = None
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


def _pdf_thumb(filepath: Path, size: int) -> Image.Image | None:
    """Render a thumbnail for a PDF file.

    filepath (Path): The path of the file.
        size (int): The size of the icon.
    """
    im: Image.Image | None = None

    file: QFile = QFile(filepath)
    success: bool = file.open(QIODeviceBase.OpenModeFlag.ReadOnly, QFileDevice.Permission.ReadUser)
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


def _text_thumb(filepath: Path, is_dark_theme: bool) -> Image.Image | None:
    """Render a thumbnail for a plaintext file.

    Args:
        filepath (Path): The path of the file.
    """
    im: Image.Image | None = None

    bg_color: str = "#1e1e1e" if is_dark_theme else "#FFFFFF"
    fg_color: str = "#FFFFFF" if is_dark_theme else "#111111"

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


def _resize_image(image: Image.Image, size: tuple[int, int]) -> Image.Image:
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


def _get_resource_id(url: Path) -> str:
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
