# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import contextlib
import hashlib
import math
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING

import structlog
from PIL import (
    Image,
    ImageChops,
    ImageDraw,
    ImageEnhance,
    ImageFile,
    ImageQt,
    UnidentifiedImageError,
)
from PIL.Image import DecompressionBombError
from PySide6.QtCore import QObject, QSize, Qt, Signal
from PySide6.QtGui import QGuiApplication, QPixmap
from typing_extensions import deprecated

from tagstudio.core.exceptions import NoRendererError
from tagstudio.core.library.ignore import Ignore
from tagstudio.core.media_types import MediaCategories, MediaType
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.global_settings import (
    DEFAULT_CACHED_THUMB_RES,
    MAX_CACHED_THUMB_RES,
    MIN_CACHED_THUMB_RES,
)
from tagstudio.qt.helpers.gradients import four_corner_gradient
from tagstudio.qt.models.palette import UI_COLORS, ColorType, UiColor, get_ui_color
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.renderers.archive import (
    apple_embedded_thumb,
    archive_thumb,
    krita_thumb,
    open_doc_thumb,
    powerpoint_thumb,
)
from tagstudio.renderers.audio import audio_album_thumb, audio_waveform_thumb
from tagstudio.renderers.blender import blender
from tagstudio.renderers.clip_studio import clip_thumb, pdn_thumb
from tagstudio.renderers.ebook import epub_cover
from tagstudio.renderers.font import font_long_thumb, font_short_thumb
from tagstudio.renderers.medibang_paint import mdp_thumb
from tagstudio.renderers.pdf import pdf_thumb
from tagstudio.renderers.raster_image import image_exr_thumb, image_raw_thumb, image_thumb
from tagstudio.renderers.source_engine import vtf_thumb
from tagstudio.renderers.text import text_thumb
from tagstudio.renderers.vector_image import image_vector_thumb
from tagstudio.renderers.video import video_thumb

if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None


logger = structlog.get_logger(__name__)


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

    @deprecated("This method will be replaced with Qt painting methods in the near future.")
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

    @deprecated("This method will be replaced with Qt painting methods in the near future.")
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

    @deprecated("This method will be replaced with Qt painting methods in the near future.")
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
            size=tuple([d * smooth_factor for d in size]),  # pyright: ignore[reportArgumentType]
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

    @deprecated("This method will be replaced with Qt painting methods in the near future.")
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
            size=tuple([d * smooth_factor for d in size]),  # pyright: ignore[reportArgumentType]
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
            size=tuple([d * smooth_factor for d in size]),  # pyright: ignore[reportArgumentType]
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
            size=tuple([d * smooth_factor for d in size]),  # pyright: ignore[reportArgumentType]
            color="#FF000000",
        )

        # Create solid background color
        bg: Image.Image
        bg = Image.new(
            "RGB",
            size=tuple([d * smooth_factor for d in size]),  # pyright: ignore[reportArgumentType]
            color="#000000FF",
        )

        # Use a background image if provided
        if bg_image:
            bg_im = Image.Image.resize(bg_image, size=tuple([d * smooth_factor for d in size]))  # pyright: ignore[reportArgumentType]
            bg_im = ImageEnhance.Brightness(bg_im).enhance(0.3)  # Reduce the brightness
            bg.paste(bg_im)

        # Paste background color with rounded rectangle mask onto blank image
        im.paste(
            bg,
            (0, 0),
            mask=self._get_mask(
                tuple([d * smooth_factor for d in size]),  # pyright: ignore[reportArgumentType]
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
        icon = self.rm.get(name)
        assert isinstance(icon, Image.Image) or icon is None
        if not icon:
            icon = self.rm.file_generic

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
            size=tuple([d * smooth_factor for d in size]),  # pyright: ignore[reportArgumentType]
            color="#00000000",
        )

        bg: Image.Image
        # Use a background image if provided
        if bg_image:
            bg = Image.Image.resize(bg_image, size=tuple([d * smooth_factor for d in size]))  # pyright: ignore[reportArgumentType]
        # Create solid background color
        else:
            bg = Image.new(
                "RGB",
                size=tuple([d * smooth_factor for d in size]),  # pyright: ignore[reportArgumentType]
                color="#000000",
            )
            # Apply color overlay
            bg = self._apply_overlay_color(
                im,
                color,
            )

        # Paste background color with rounded rectangle mask onto blank image
        im.paste(
            bg,
            (0, 0),
            mask=self._get_mask(
                tuple([d * smooth_factor for d in size]),  # pyright: ignore[reportArgumentType]
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
        icon = self.rm.get(name)
        assert isinstance(icon, Image.Image)
        if not icon:
            icon = self.rm.file_generic

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

    @deprecated("This method will be replaced with Qt painting methods in the near future.")
    def _apply_edge(
        self, image: Image.Image, edge: tuple[Image.Image, Image.Image], faded: bool = False
    ) -> Image.Image:
        """Apply a given edge effect to an image.

        Args:
            image (Image.Image): The image to apply the edge to.
            edge (tuple[Image.Image, Image.Image]): The edge images to apply.
                Item 0 is the inner highlight, and item 1 is the outer shadow.
            faded (bool): Whether to apply a faded version of the edge.
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
            timestamp (float): The timestamp for which this job was dispatched.
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
            icon: Image.Image = self.rm.ignored

            icon = icon.resize((math.ceil(size[0] // icon_ratio), math.ceil(size[1] // icon_ratio)))

            im_.paste(
                im=icon.resize(
                    (math.ceil(size[0] // icon_ratio), math.ceil(size[1] // icon_ratio))
                ),
                box=(size[0] // padding_factor, size[1] // padding_factor),
                mask=icon.getchannel(3),
            )

            return im_

        def fetch_cached_image(file_name: Path):
            image: Image.Image | None = None
            assert self.driver.cache_manager is not None
            cached_path = self.driver.cache_manager.get_file_path(file_name)

            if cached_path and cached_path.is_file():
                try:
                    image = Image.open(cached_path)
                    if not image:
                        raise UnidentifiedImageError  # pyright: ignore[reportUnreachable]
                except Exception as e:
                    logger.error(
                        "[ThumbRenderer] Couldn't open cached thumbnail!", path=cached_path, error=e
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
                settings_res = self.driver.settings.cached_thumb_resolution
                thumb_res = (
                    settings_res
                    if settings_res >= MIN_CACHED_THUMB_RES and settings_res <= MAX_CACHED_THUMB_RES
                    else DEFAULT_CACHED_THUMB_RES
                )

                # Render from file, return result, and try to save a cached version.
                # TODO: Audio waveforms are dynamically sized based on the base_size, so hardcoding
                # the resolution breaks that.
                image = self._render(
                    timestamp,
                    filepath,
                    (thumb_res, thumb_res),
                    1,
                    is_grid_thumb,
                    save_to_file=file_name,
                )

            # If the normal renderer failed, fallback the defaults
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
            self.updated.emit(timestamp, QPixmap(), QSize(*base_size), filepath)

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
            timestamp (float): The timestamp for which this job was dispatched.
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
                # Ebooks =======================================================
                if MediaCategories.is_ext_in_category(
                    ext, MediaCategories.EBOOK_TYPES, mime_fallback=True
                ):
                    image = epub_cover(_filepath, ext)
                # Krita ========================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.KRITA_TYPES, mime_fallback=True
                ):
                    image = krita_thumb(_filepath)
                # Clip Studio Paint ============================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.CLIP_STUDIO_PAINT_TYPES
                ):
                    image = clip_thumb(_filepath)
                # VTF ==========================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.SOURCE_ENGINE_TYPES, mime_fallback=True
                ):
                    image = vtf_thumb(_filepath)
                # Images =======================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.IMAGE_TYPES, mime_fallback=True
                ):
                    # Raw Images -----------------------------------------------
                    if MediaCategories.is_ext_in_category(
                        ext, MediaCategories.IMAGE_RAW_TYPES, mime_fallback=True
                    ):
                        image = image_raw_thumb(_filepath)
                    # Vector Images --------------------------------------------
                    elif MediaCategories.is_ext_in_category(
                        ext, MediaCategories.IMAGE_VECTOR_TYPES, mime_fallback=True
                    ):
                        image = image_vector_thumb(_filepath, adj_size)
                    # EXR Images -----------------------------------------------
                    elif ext in [".exr"]:
                        image = image_exr_thumb(_filepath)
                    # Normal Images --------------------------------------------
                    else:
                        image = image_thumb(_filepath)
                # Videos =======================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.VIDEO_TYPES, mime_fallback=True
                ):
                    image = video_thumb(_filepath)
                # PowerPoint Slideshow
                elif ext in {".pptx"}:
                    image = powerpoint_thumb(_filepath)
                # OpenDocument/OpenOffice ======================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.OPEN_DOCUMENT_TYPES, mime_fallback=True
                ):
                    image = open_doc_thumb(_filepath)
                # Apple iWork Suite ============================================
                elif (
                    MediaCategories.is_ext_in_category(ext, MediaCategories.IWORK_TYPES)
                    or ext == ".pxd"
                ):
                    image = apple_embedded_thumb(_filepath)
                # Plain Text ===================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.PLAINTEXT_TYPES, mime_fallback=True
                ):
                    image = text_thumb(_filepath)
                # Fonts ========================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.FONT_TYPES, mime_fallback=True
                ):
                    if is_grid_thumb:
                        # Short (Aa) Preview
                        image = font_short_thumb(_filepath, adj_size)
                        if image is not None:
                            image = self._apply_overlay_color(image, UiColor.BLUE)
                    else:
                        # Large (Full Alphabet) Preview
                        image = font_long_thumb(_filepath, adj_size)
                # Audio ========================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.AUDIO_TYPES, mime_fallback=True
                ):
                    image = audio_album_thumb(_filepath, ext)
                    if image is None:
                        image = audio_waveform_thumb(_filepath, ext, adj_size, pixel_ratio)
                        savable_media_type = False
                        if image is not None:
                            image = self._apply_overlay_color(image, UiColor.GREEN)
                # Blender ======================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.BLENDER_TYPES, mime_fallback=True
                ):
                    image = blender(_filepath)
                # PDF ==========================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.PDF_TYPES, mime_fallback=True
                ):
                    image = pdf_thumb(_filepath, adj_size, ext)
                # Archives =====================================================
                elif MediaCategories.is_ext_in_category(ext, MediaCategories.ARCHIVE_TYPES):
                    image = archive_thumb(_filepath, ext)
                # MDIPACK ======================================================
                elif MediaCategories.is_ext_in_category(ext, MediaCategories.MDIPACK_TYPES):
                    image = mdp_thumb(_filepath)
                # Paint.NET ====================================================
                elif MediaCategories.is_ext_in_category(ext, MediaCategories.PAINT_DOT_NET_TYPES):
                    image = pdn_thumb(_filepath)
                # No Rendered Thumbnail ========================================
                if not image:
                    raise NoRendererError

                if image:
                    image = self._resize_image(image, (adj_size, adj_size))

                if save_to_file and savable_media_type and image:
                    assert self.driver.cache_manager is not None
                    self.driver.cache_manager.save_image(image, save_to_file, mode="RGBA")

            except (
                AssertionError,
                ChildProcessError,
                DecompressionBombError,
                UnidentifiedImageError,
                ValueError,
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
