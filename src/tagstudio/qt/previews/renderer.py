# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import contextlib
import hashlib
import math
import os
import zipfile
from copy import deepcopy
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np
import pillow_avif  # noqa: F401 # pyright: ignore[reportUnusedImport]
import rawpy
import structlog
from PIL import (
    Image,
    ImageChops,
    ImageDraw,
    ImageEnhance,
    ImageFile,
    ImageOps,
    ImageQt,
    UnidentifiedImageError,
)
from PIL.Image import DecompressionBombError
from pillow_heif import register_heif_opener
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

from tagstudio.core.exceptions import NoRendererError
from tagstudio.core.library.ignore import Ignore
from tagstudio.core.media_types import MediaCategories, MediaType
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.global_settings import DEFAULT_CACHED_IMAGE_RES
from tagstudio.qt.helpers.gradients import four_corner_gradient
from tagstudio.qt.helpers.image_effects import apply_overlay_color, replace_transparent_pixels
from tagstudio.qt.models.palette import UI_COLORS, ColorType, UiColor
from tagstudio.qt.previews.renderer_type import RendererType
from tagstudio.qt.previews.renderers.base_renderer import RendererContext
from tagstudio.qt.previews.vendored.blender_renderer import blend_thumb
from tagstudio.qt.resource_manager import ResourceManager

if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

ImageFile.LOAD_TRUNCATED_IMAGES = True
os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"

logger = structlog.get_logger(__name__)
Image.MAX_IMAGE_PIXELS = None
register_heif_opener()

try:
    import pillow_jxl  # noqa: F401 # pyright: ignore[reportUnusedImport]
except ImportError:
    logger.exception('[ThumbRenderer] Could not import the "pillow_jxl" module')


class ThumbRenderer(QObject):
    """A class for rendering image and file thumbnails."""

    rm: ResourceManager = ResourceManager()
    updated = Signal(float, QPixmap, QSize, Path)
    updated_ratio = Signal(float)
    cached_img_ext: str = ".webp"

    def __init__(self, driver: "QtDriver") -> None:
        """Initialize the class."""
        super().__init__()
        self.driver = driver

        settings_res = self.driver.settings.cached_thumb_resolution
        self.cached_img_res = (
            settings_res
            if settings_res >= 16 and settings_res <= 2048
            else DEFAULT_CACHED_IMAGE_RES
        )

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
        self,
        name: str,
        color: UiColor,
        size: tuple[int, int],
        pixel_ratio: float = 1.0,
        bg_image: Image.Image | None = None,
        draw_edge: bool = True,
        is_corner: bool = False,
    ) -> Image.Image:
        """Return an icon given a size, pixel ratio, and radius scaling option.

        Args:
            name (str): The name of the icon resource. "thumb_loading" will not draw a border.
            color (str): The color to use for the icon.
            size (tuple[int,int]): The size of the icon.
            pixel_ratio (float): The screen pixel ratio.
            bg_image (Image.Image): Optional background image to go behind the icon.
            draw_edge (bool): Flag for is the raised edge should be drawn.
            is_corner (bool): Flag for is the icon should render with the "corner" style
        """
        draw_border: bool = True
        if name == "thumb_loading":
            draw_border = False

        item: Image.Image | None = self.icons.get((name, color, *size, pixel_ratio))
        if not item:
            item_flat: Image.Image = (
                self._render_corner_icon(name, color, size, pixel_ratio, bg_image)
                if is_corner
                else self._render_center_icon(name, color, size, pixel_ratio, draw_border, bg_image)
            )
            if draw_edge:
                edge: tuple[Image.Image, Image.Image] = self._get_edge(size, pixel_ratio)
                item = self._apply_edge(item_flat, edge, faded=True)
                self.icons[(name, color, *size, pixel_ratio)] = item
            else:
                item = item_flat
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
            size=([d * smooth_factor for d in size]),
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
            size=([d * smooth_factor for d in size]),
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
            size=([d * smooth_factor for d in size]),
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

    def _render_center_icon(
        self,
        name: str,
        color: UiColor,
        size: tuple[int, int],
        pixel_ratio: float,
        draw_border: bool = True,
        bg_image: Image.Image | None = None,
    ) -> Image.Image:
        """Render a thumbnail icon.

        Args:
            name (str): The name of the icon resource.
            color (UiColor): The color to use for the icon.
            size (tuple[int,int]): The size of the icon.
            pixel_ratio (float): The screen pixel ratio.
            draw_border (bool): Option to draw a border.
            bg_image (Image.Image): Optional background image to go behind the icon.
        """
        border_factor: int = 5
        smooth_factor: int = math.ceil(2 * pixel_ratio)
        radius_factor: int = 8
        icon_ratio: float = 1.75

        # Create larger blank image based on smooth_factor
        im: Image.Image = Image.new(
            "RGBA",
            size=([d * smooth_factor for d in size]),
            color="#FF000000",
        )

        # Create solid background color
        bg: Image.Image
        bg = Image.new(
            "RGB",
            size=([d * smooth_factor for d in size]),
            color="#000000FF",
        )

        # Use a background image if provided
        if bg_image:
            bg_im = Image.Image.resize(bg_image, size=([d * smooth_factor for d in size]))
            bg_im = ImageEnhance.Brightness(bg_im).enhance(0.3)  # Reduce the brightness
            bg.paste(bg_im)

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
                fill=None if bg_image else "black",
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
        icon: Image.Image | None = self.rm.get(name)  # pyright: ignore[reportAssignmentType]
        if not icon:
            icon = self.rm.get("file_generic")  # pyright: ignore[reportAssignmentType]
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
        im = apply_overlay_color(
            im,
            color,
        )

        return im

    def _render_corner_icon(
        self,
        name: str,
        color: UiColor,
        size: tuple[int, int],
        pixel_ratio: float,
        bg_image: Image.Image | None = None,
    ) -> Image.Image:
        """Render a thumbnail icon with the icon in the upper-left corner.

        Args:
            name (str): The name of the icon resource.
            color (UiColor): The color to use for the icon.
            size (tuple[int,int]): The size of the icon.
            pixel_ratio (float): The screen pixel ratio.
            draw_border (bool): Option to draw a border.
            bg_image (Image.Image): Optional background image to go behind the icon.
        """
        smooth_factor: int = math.ceil(2 * pixel_ratio)
        icon_ratio: float = 5
        padding_factor = 18

        # Create larger blank image based on smooth_factor
        im: Image.Image = Image.new(
            "RGBA",
            size=([d * smooth_factor for d in size]),
            color="#00000000",
        )

        bg: Image.Image
        # Use a background image if provided
        if bg_image:
            bg = Image.Image.resize(bg_image, size=([d * smooth_factor for d in size]))
        # Create solid background color
        else:
            bg = Image.new(
                "RGB",
                size=([d * smooth_factor for d in size]),
                color="#000000",
            )
            # Apply color overlay
            bg = apply_overlay_color(
                im,
                color,
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

        colors = UI_COLORS.get(color) or UI_COLORS[UiColor.DEFAULT]
        primary_color = colors.get(ColorType.PRIMARY)

        # Resize image to final size
        im = im.resize(
            size,
            resample=Image.Resampling.BILINEAR,
        )
        fg: Image.Image = Image.new(
            "RGB",
            size=size,
            color=primary_color,
        )

        # Get icon by name
        icon: Image.Image | None = self.rm.get(name)  # pyright: ignore[reportAssignmentType]
        if not icon:
            icon = self.rm.get("file_generic")  # pyright: ignore[reportAssignmentType]
            if not icon:
                icon = Image.new(mode="RGBA", size=(32, 32), color="magenta")

        # Resize icon to fit icon_ratio
        icon = icon.resize(
            (
                math.ceil(size[0] // icon_ratio),
                math.ceil(size[1] // icon_ratio),
            )
        )

        # Paste icon
        im.paste(
            im=fg.resize(
                (
                    math.ceil(size[0] // icon_ratio),
                    math.ceil(size[1] // icon_ratio),
                )
            ),
            box=(size[0] // padding_factor, size[1] // padding_factor),
            mask=icon.getchannel(3),
        )

        return im

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
    def _blender(filepath: Path) -> Image.Image | None:
        """Get an emended thumbnail from a Blender file, if a thumbnail is present.

        Args:
            filepath (Path): The path of the file.
        """
        bg_color: str = (
            "#1e1e1e"
            if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
            else "#FFFFFF"
        )
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

    @staticmethod
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
            rawpy._rawpy.LibRawIOError,  # pyright: ignore[reportAttributeAccessIssue]
            rawpy._rawpy.LibRawFileUnsupportedError,  # pyright: ignore[reportAttributeAccessIssue]
        ) as e:
            logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
        return im

    @staticmethod
    def _image_exr_thumb(filepath: Path) -> Image.Image | None:
        """Render a thumbnail for a EXR image type.

        Args:
            filepath (Path): The path of the file.
        """
        im: Image.Image | None = None
        try:
            # Load the EXR data to an array and rotate the color space from BGRA -> RGBA
            raw_array = cv2.imread(str(filepath), cv2.IMREAD_UNCHANGED)
            raw_array[..., :3] = raw_array[..., 2::-1]

            # Correct the gamma of the raw array
            gamma = 2.2
            array_gamma = np.power(np.clip(raw_array, 0, 1), 1 / gamma)
            array = (array_gamma * 255).astype(np.uint8)

            im = Image.fromarray(array, mode="RGBA")

            # Paste solid background
            if im.mode == "RGBA":
                new_bg = Image.new("RGB", im.size, color="#1e1e1e")
                new_bg.paste(im, mask=im.getchannel(3))
                im = new_bg

        except Exception as e:
            logger.error("Couldn't render thumbnail", filepath=filepath, error=type(e).__name__)
        return im

    @staticmethod
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
            im = unwrap(ImageOps.exif_transpose(im))
        except (
            FileNotFoundError,
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def _pdf_thumb(filepath: Path, size: int) -> Image.Image | None:
        """Render a thumbnail for a PDF file.

        filepath (Path): The path of the file.
            size (int): The size of the icon.
        """
        im: Image.Image | None = None

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

        def render_unlinked(
            size: tuple[int, int], pixel_ratio: float, cached_im: Image.Image | None = None
        ) -> Image.Image:
            im = self._get_icon(
                name="broken_link_icon",
                color=UiColor.RED,
                size=size,
                pixel_ratio=pixel_ratio,
                bg_image=cached_im,
                draw_edge=not cached_im,
                is_corner=False,
            )
            return im

        def render_ignored(
            size: tuple[int, int], pixel_ratio: float, im: Image.Image
        ) -> Image.Image:
            icon_ratio: float = 5
            padding_factor = 18

            im_ = im
            icon: Image.Image = self.rm.get("ignored")  # pyright: ignore[reportAssignmentType]

            icon = icon.resize(
                (
                    math.ceil(size[0] // icon_ratio),
                    math.ceil(size[1] // icon_ratio),
                )
            )

            im_.paste(
                im=icon.resize(
                    (
                        math.ceil(size[0] // icon_ratio),
                        math.ceil(size[1] // icon_ratio),
                    )
                ),
                box=(size[0] // padding_factor, size[1] // padding_factor),
                mask=icon.getchannel(3),
            )

            return im_

        def fetch_cached_image(file_name: Path):
            image: Image.Image | None = None
            cached_path = self.driver.cache_manager.get_file_path(file_name)

            if cached_path and cached_path.is_file():
                try:
                    image = Image.open(cached_path)
                    if not image:
                        raise UnidentifiedImageError  # pyright: ignore[reportUnreachable]
                except Exception as e:
                    logger.error(
                        "[ThumbRenderer] Couldn't open cached thumbnail!",
                        path=cached_path,
                        error=e,
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
            file_name = Path(f"{hash_value}{ThumbRenderer.cached_img_ext}")
            image = fetch_cached_image(file_name)

            if not image and self.driver.settings.generate_thumbs:
                # Render from file, return result, and try to save a cached version.
                # TODO: Audio waveforms are dynamically sized based on the base_size, so hardcoding
                # the resolution breaks that.
                image = self._render(
                    timestamp,
                    filepath,
                    (self.cached_img_res, self.cached_img_res),
                    1,
                    is_grid_thumb,
                    save_to_file=file_name,
                )

            # If the normal renderer failed, fallback the the defaults
            # (with native non-cached sizing!)
            if not image:
                image = (
                    render_unlinked((adj_size, adj_size), pixel_ratio)
                    if not filepath.exists() or filepath.is_dir()
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

            # Check if the file is supposed to be ignored and render an overlay if needed
            try:
                if (
                    image
                    and Ignore.compiled_patterns
                    and Ignore.compiled_patterns.match(
                        filepath.relative_to(unwrap(self.driver.lib.library_dir))
                    )
                ):
                    image = render_ignored((adj_size, adj_size), pixel_ratio, image)
            except TypeError:
                pass

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
                    if not filepath.exists() or filepath.is_dir()
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
            )
        else:
            self.updated.emit(
                timestamp,
                QPixmap(),
                QSize(*base_size),
                filepath,
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

        if _filepath and _filepath.is_file():
            try:
                ext: str = _filepath.suffix.lower() if _filepath.suffix else _filepath.stem.lower()

                renderer_type: RendererType | None = RendererType.get_renderer_type(ext)
                renderer_context: RendererContext = RendererContext(
                    path=_filepath,
                    extension=ext,
                    size=adj_size,
                    pixel_ratio=pixel_ratio,
                    is_grid_thumb=is_grid_thumb,
                )

                logger.debug(
                    "[ThumbRenderer]",
                    renderer_type=renderer_type,
                    renderer_context=renderer_context,
                )
                if renderer_type:
                    image = renderer_type.renderer.render(renderer_context)

                # Images =======================================================
                elif MediaCategories.is_ext_in_category(
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
                    # EXR Images -----------------------------------------------
                    elif ext in [".exr"]:
                        image = self._image_exr_thumb(_filepath)
                    # Normal Images --------------------------------------------
                    else:
                        image = self._image_thumb(_filepath)
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
                # No Rendered Thumbnail ========================================
                if not image:
                    raise NoRendererError

                if image:
                    image = self._resize_image(image, (adj_size, adj_size))

                if save_to_file and savable_media_type and image:
                    self.driver.cache_manager.save_image(image, save_to_file, mode="RGBA")

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
