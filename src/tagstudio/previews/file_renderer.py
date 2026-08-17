# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import contextlib
import hashlib
import math
from copy import deepcopy
from pathlib import Path

import structlog
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFile, UnidentifiedImageError
from PIL.Image import DecompressionBombError

from tagstudio.core.exceptions import NoRendererError
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.ignore import Ignore
from tagstudio.core.media_types import MediaCategories, MediaType
from tagstudio.core.utils.types import unwrap
from tagstudio.previews.gradients import four_corner_gradient
from tagstudio.previews.renderers.archive import (
    apple_embedded_thumb,
    archive_thumb,
    krita_thumb,
    open_doc_thumb,
    powerpoint_thumb,
)
from tagstudio.previews.renderers.audio import audio_album_thumb, audio_waveform_thumb
from tagstudio.previews.renderers.blender import blender_thumb
from tagstudio.previews.renderers.clip_studio import clip_studio_thumb
from tagstudio.previews.renderers.ebook import epub_thumb
from tagstudio.previews.renderers.font import font_full_preview, font_small_thumb
from tagstudio.previews.renderers.medibang_paint import medibang_paint_thumb
from tagstudio.previews.renderers.paint_dot_net import paint_dot_net_thumb
from tagstudio.previews.renderers.pdf import pdf_thumb
from tagstudio.previews.renderers.raster_image import (
    exr_image_thumb,
    raster_image_thumb,
    raw_image_thumb,
)
from tagstudio.previews.renderers.source_engine import vtf_thumb
from tagstudio.previews.renderers.text import text_thumb
from tagstudio.previews.renderers.vector_image import vector_image_thumb
from tagstudio.previews.renderers.video import video_thumb
from tagstudio.qt.app_settings import (
    DEFAULT_CACHED_THUMB_RES,
    MAX_CACHED_THUMB_RES,
    MIN_CACHED_THUMB_RES,
    AppSettings,
    Theme,
)
from tagstudio.qt.cache_manager import CacheManager
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.styles.palette import UI_COLORS, ColorType, UiColor, get_ui_color

ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None


logger = structlog.get_logger(__name__)


class FileRenderer:
    """A class for rendering image previews and thumbnails from files."""

    rm: ResourceManager = ResourceManager()
    cached_img_ext: str = ".webp"

    def __init__(self, library: Library, settings: AppSettings) -> None:
        super().__init__()
        self.lib = library
        self.settings = settings

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

    # NOTE: This method will be replaced with frontend specific decorations (Qt painting)
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

    # NOTE: This method will be replaced with frontend specific decorations (Qt painting)
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
        theme: Theme,
        dpi_scale: float = 1.0,
        bg_image: Image.Image | None = None,
        draw_edge: bool = True,
        is_corner: bool = False,
    ) -> Image.Image:
        """Return an icon given a size, pixel ratio, and radius scaling option.

        Args:
            name (str): The name of the icon resource. "thumb_loading" will not draw a border.
            color (str): The color to use for the icon.
            size (tuple[int,int]): The size of the icon.
            theme (Theme): A theme enum to determine the light/dark theme.
            dpi_scale (float): The screen pixel ratio.
            bg_image (Image.Image): Optional background image to go behind the icon.
            draw_edge (bool): Flag for is the raised edge should be drawn.
            is_corner (bool): Flag for is the icon should render with the "corner" style
        """
        draw_border: bool = True
        if name == "thumb_loading":
            draw_border = False

        item: Image.Image | None = self.icons.get((name, color, *size, dpi_scale))
        if not item:
            item_flat: Image.Image = (
                self._render_corner_icon(name, color, size, dpi_scale, theme, bg_image)
                if is_corner
                else self._render_center_icon(
                    name, color, size, dpi_scale, theme, draw_border, bg_image
                )
            )
            if draw_edge:
                edge: tuple[Image.Image, Image.Image] = self._get_edge(size, dpi_scale)
                item = self._apply_edge(item_flat, edge, theme, faded=True)
                self.icons[(name, color, *size, dpi_scale)] = item
            else:
                item = item_flat
        return item

    # NOTE: This method will be replaced with frontend specific decorations (Qt painting)
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

    # NOTE: This method will be replaced with frontend specific decorations (Qt painting)
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
        im_hl = im_hl.resize(size, resample=Image.Resampling.BILINEAR)

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
        im_sh = im_sh.resize(size, resample=Image.Resampling.BILINEAR)

        return (im_hl, im_sh)

    def _render_center_icon(
        self,
        name: str,
        color: UiColor,
        size: tuple[int, int],
        pixel_ratio: float,
        theme: Theme,
        draw_border: bool = True,
        bg_image: Image.Image | None = None,
    ) -> Image.Image:
        """Render a thumbnail icon.

        Args:
            name (str): The name of the icon resource.
            color (UiColor): The color to use for the icon.
            size (tuple[int,int]): The size of the icon.
            pixel_ratio (float): The screen pixel ratio.
            theme (Theme): A theme enum to determine the light/dark theme.
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
        im = im.resize(size, resample=Image.Resampling.BILINEAR)
        fg: Image.Image = Image.new("RGB", size=size, color="#00FF00")

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
        im = self._apply_overlay_color(im, color, theme)

        return im

    def _render_corner_icon(
        self,
        name: str,
        color: UiColor,
        size: tuple[int, int],
        pixel_ratio: float,
        theme: Theme,
        bg_image: Image.Image | None = None,
    ) -> Image.Image:
        """Render a thumbnail icon with the icon in the upper-left corner.

        Args:
            name (str): The name of the icon resource.
            color (UiColor): The color to use for the icon.
            size (tuple[int,int]): The size of the icon.
            pixel_ratio (float): The screen pixel ratio.
            theme (Theme): A theme enum to determine the light/dark theme.
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
            bg = self._apply_overlay_color(im, color, theme)

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
        im = im.resize(size, resample=Image.Resampling.BILINEAR)
        fg: Image.Image = Image.new("RGB", size=size, color=primary_color)

        # Get icon by name
        icon = self.rm.get(name)
        assert isinstance(icon, Image.Image)
        if not icon:
            icon = self.rm.file_generic

        # Resize icon to fit icon_ratio
        icon = icon.resize((math.ceil(size[0] // icon_ratio), math.ceil(size[1] // icon_ratio)))

        # Paste icon
        im.paste(
            im=fg.resize((math.ceil(size[0] // icon_ratio), math.ceil(size[1] // icon_ratio))),
            box=(size[0] // padding_factor, size[1] // padding_factor),
            mask=icon.getchannel(3),
        )

        return im

    def _apply_overlay_color(self, image: Image.Image, color: UiColor, theme: Theme) -> Image.Image:
        """Apply a color overlay effect to an image based on its color channel data.

        Red channel for foreground, green channel for outline, none for background.

        Args:
            image (Image.Image): The image to apply an overlay to.
            color (UiColor): The name of the ColorType color to use.
            theme (Theme): A theme enum to determine the light/dark theme.
        """
        bg_color: str = (
            get_ui_color(ColorType.DARK_ACCENT, color)
            if theme == Theme.DARK
            else get_ui_color(ColorType.PRIMARY, color)
        )
        fg_color: str = (
            get_ui_color(ColorType.PRIMARY, color)
            if theme == Theme.DARK
            else get_ui_color(ColorType.LIGHT_ACCENT, color)
        )
        ol_color: str = (
            get_ui_color(ColorType.BORDER, color)
            if theme == Theme.DARK
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

    # NOTE: This method will be replaced with frontend specific decorations (Qt painting)
    def _apply_edge(
        self,
        image: Image.Image,
        edge: tuple[Image.Image, Image.Image],
        theme: Theme,
        faded: bool = False,
    ) -> Image.Image:
        """Apply a given edge effect to an image.

        Args:
            image (Image.Image): The image to apply the edge to.
            edge (tuple[Image.Image, Image.Image]): The edge images to apply.
                Item 0 is the inner highlight, and item 1 is the outer shadow.
            theme (Theme): A theme enum to determine the light/dark theme.
            faded (bool): Whether to apply a faded version of the edge.
                Used for light themes.
        """
        opacity: float = 1.0 if not faded else 0.8
        shade_reduction: float = 0 if theme == Theme.DARK else 0.3
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
        cache: CacheManager | None,
        timestamp: float,
        filepath: Path | str,
        size: tuple[int, int],
        dpi_scale: float,
        theme: Theme = Theme.DARK,
        is_loading: bool = False,
        is_thumb: bool = False,
    ):
        """Render a thumbnail or preview image.

        Args:
            cache (CacheManager | None): A cache manager instance.
            timestamp (float): The timestamp for which this job was dispatched.
            filepath (str | Path): The path of the file to render a thumbnail for.
            size (tuple[int, int]): The unmodified base size of the thumbnail.
            dpi_scale (float): The screen pixel ratio.
            theme (Theme): A theme enum to determine the light/dark theme.
            is_loading (bool): Is this a loading graphic?
            is_thumb (bool): Is this specifically a thumbnail? Use for specifying small variants.
            update_on_ratio_change (bool): Should an updated ratio signal be sent?
        """
        render_mask_and_edge: bool = True
        scaled_size = math.ceil(max(size[0], size[1]) * dpi_scale)
        theme_color: UiColor = UiColor.THEME_LIGHT if theme == Theme.LIGHT else UiColor.THEME_DARK
        if isinstance(filepath, str):
            filepath = Path(filepath)

        def render_default(size: tuple[int, int], dpi_scale: float) -> Image.Image:
            im = self._get_icon(
                name=self._get_resource_id(filepath),
                color=theme_color,
                size=size,
                theme=theme,
                dpi_scale=dpi_scale,
            )
            return im

        def render_unlinked(
            size: tuple[int, int], dpi_scale: float, cached_im: Image.Image | None = None
        ) -> Image.Image:
            im = self._get_icon(
                name="broken_link_icon",
                color=UiColor.RED,
                size=size,
                theme=theme,
                dpi_scale=dpi_scale,
                bg_image=cached_im,
                draw_edge=not cached_im,
                is_corner=False,
            )
            return im

        def render_ignored(size: tuple[int, int], im: Image.Image) -> Image.Image:
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
            if not cache:
                return image
            cached_path = cache.get_file_path(file_name)

            if cached_path and cached_path.is_file():
                try:
                    image = Image.open(cached_path)
                    if not image:
                        raise UnidentifiedImageError  # pyright: ignore[reportUnreachable]
                except Exception as e:
                    logger.error(
                        "[FileRenderer] Couldn't open cached thumbnail!", path=cached_path, error=e
                    )
            return image

        image: Image.Image | None = None
        # Try to get a non-loading thumbnail for the grid.
        if not is_loading and is_thumb and filepath and filepath != Path("."):
            # Attempt to retrieve cached image from disk
            mod_time: str = ""
            with contextlib.suppress(Exception):
                mod_time = str(filepath.stat().st_mtime_ns)
            hashable_str: str = f"{str(filepath)}{mod_time}"
            hash_value = hashlib.shake_128(hashable_str.encode("utf-8")).hexdigest(8)
            file_name = Path(f"{hash_value}{FileRenderer.cached_img_ext}")
            image = fetch_cached_image(file_name)

            if not image and self.settings.generate_thumbs:
                settings_res = self.settings.cached_thumb_resolution
                thumb_res = (
                    settings_res
                    if settings_res >= MIN_CACHED_THUMB_RES and settings_res <= MAX_CACHED_THUMB_RES
                    else DEFAULT_CACHED_THUMB_RES
                )

                # Render from file, return result, and try to save a cached version.
                # TODO: Audio waveforms are dynamically sized based on the base_size, so hardcoding
                # the resolution breaks that.
                image = self._render(
                    cache=cache,
                    filepath=filepath,
                    size=(thumb_res, thumb_res),
                    dpi_scale=1,
                    theme=theme,
                    is_thumb=is_thumb,
                    cache_filename=file_name,
                )

            # If the normal renderer failed, fallback the defaults
            # (with native non-cached sizing!)
            if not image:
                image = (
                    render_unlinked((scaled_size, scaled_size), dpi_scale)
                    if not filepath.exists() or filepath.is_dir()
                    else render_default((scaled_size, scaled_size), dpi_scale)
                )
                render_mask_and_edge = False

            # Apply the mask and edge
            if image:
                image = self._resize_image(image, (scaled_size, scaled_size))
                if render_mask_and_edge:
                    mask = self._get_mask((scaled_size, scaled_size), dpi_scale)
                    edge: tuple[Image.Image, Image.Image] = self._get_edge(
                        (scaled_size, scaled_size), dpi_scale
                    )
                    image = self._apply_edge(
                        four_corner_gradient(image, (scaled_size, scaled_size), mask), edge, theme
                    )

            # Check if the file is supposed to be ignored and render an overlay if needed
            try:
                if (
                    image
                    and Ignore.compiled_patterns
                    and Ignore.compiled_patterns.match(
                        filepath.relative_to(unwrap(self.lib.library_dir))
                    )
                ):
                    image = render_ignored((scaled_size, scaled_size), image)
            except TypeError:
                pass

        # A loading thumbnail (cached in memory)
        elif is_loading:
            # Initialize "Loading" thumbnail
            loading_thumb: Image.Image = self._get_icon(
                "thumb_loading", theme_color, (scaled_size, scaled_size), theme, dpi_scale
            )
            image = loading_thumb.resize(
                (scaled_size, scaled_size), resample=Image.Resampling.BILINEAR
            )

        # A full preview image (never cached)
        elif not is_thumb:
            image = self._render(cache, filepath, size, dpi_scale, theme)
            if not image:
                image = (
                    render_unlinked((512, 512), 2)
                    if not filepath.exists() or filepath.is_dir()
                    else render_default((512, 512), 2)
                )
                render_mask_and_edge = False
            mask = self._get_mask(image.size, dpi_scale, scale_radius=True)
            bg = Image.new("RGBA", image.size, (0, 0, 0, 0))
            bg.paste(image, mask=mask.getchannel(0))
            image = bg

        # If the image couldn't be rendered, use a default media image.
        if not image:
            image = Image.new("RGBA", (128, 128), color="#FF00FF")

        return (
            image,
            (math.ceil(scaled_size / dpi_scale), math.ceil(image.size[1] / dpi_scale)),
            timestamp,
        )

    def _render(
        self,
        cache: CacheManager | None,
        filepath: str | Path,
        size: tuple[int, int],
        dpi_scale: float,
        theme: Theme = Theme.DARK,
        is_thumb: bool = False,
        cache_filename: Path | None = None,
    ) -> Image.Image | None:
        """Render a thumbnail or preview image.

        Args:
            cache (CacheManager | None): A cache manager instance.
            timestamp (float): The timestamp for which this job was dispatched.
            filepath (str | Path): The path of the file to render a thumbnail for.
            size (tuple[int, int]): The unmodified base size of the thumbnail.
            dpi_scale (float): The screen pixel ratio.
            theme (Theme): A theme enum to determine the light/dark theme.
            is_thumb (bool): Is this specifically a thumbnail? Use for specifying small variants.
            cache_filename (Path | None): An optional filename to use to save to the cache.

        """
        scaled_size = math.ceil(max(size[0], size[1]) * dpi_scale)
        image: Image.Image | None = None
        filepath_: Path = Path(filepath)
        is_savable_type: bool = True

        if filepath_ and filepath_.is_file():
            try:
                ext: str = filepath_.suffix.lower() if filepath_.suffix else filepath_.stem.lower()
                # eBooks ===========================================================================
                if MediaCategories.is_ext_in_category(
                    ext, MediaCategories.EBOOK_TYPES, mime_fallback=True
                ):
                    image = epub_thumb(filepath_, ext)
                # Krita ============================================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.KRITA_TYPES, mime_fallback=True
                ):
                    image = krita_thumb(filepath_)
                # Clip Studio Paint ================================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.CLIP_STUDIO_PAINT_TYPES
                ):
                    image = clip_studio_thumb(filepath_)
                # VTF ==============================================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.SOURCE_ENGINE_TYPES, mime_fallback=True
                ):
                    image = vtf_thumb(filepath_)
                # Images ===========================================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.IMAGE_TYPES, mime_fallback=True
                ):
                    # Raw Images -------------------------------------------------------------------
                    if MediaCategories.is_ext_in_category(
                        ext, MediaCategories.IMAGE_RAW_TYPES, mime_fallback=True
                    ):
                        image = raw_image_thumb(filepath_)
                    # Vector Images ----------------------------------------------------------------
                    elif MediaCategories.is_ext_in_category(
                        ext, MediaCategories.IMAGE_VECTOR_TYPES, mime_fallback=True
                    ):
                        image = vector_image_thumb(filepath_, scaled_size)
                    # EXR Images -------------------------------------------------------------------
                    elif ext in [".exr"]:
                        image = exr_image_thumb(filepath_)
                    # Normal Images ----------------------------------------------------------------
                    else:
                        image = raster_image_thumb(filepath_)
                # Videos ===========================================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.VIDEO_TYPES, mime_fallback=True
                ):
                    image = video_thumb(filepath_)
                # PowerPoint =======================================================================
                elif ext in {".pptx"}:
                    image = powerpoint_thumb(filepath_)
                # OpenDocument/OpenOffice ==========================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.OPEN_DOCUMENT_TYPES, mime_fallback=True
                ):
                    image = open_doc_thumb(filepath_)
                # Apple iWork + Creator Studio =====================================================
                elif (
                    MediaCategories.is_ext_in_category(ext, MediaCategories.IWORK_TYPES)
                    or ext == ".pxd"
                ):
                    image = apple_embedded_thumb(filepath_)
                # Plain Text =======================================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.PLAINTEXT_TYPES, mime_fallback=True
                ):
                    image = text_thumb(filepath_)
                # Fonts ============================================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.FONT_TYPES, mime_fallback=True
                ):
                    if is_thumb:
                        # Short (Aa) Preview
                        image = font_small_thumb(filepath_, scaled_size)
                        if image is not None:
                            image = self._apply_overlay_color(image, UiColor.BLUE, theme)
                    else:
                        # Large (Full Alphabet) Preview
                        image = font_full_preview(filepath_, scaled_size)
                # Audio ========================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.AUDIO_TYPES, mime_fallback=True
                ):
                    image = audio_album_thumb(filepath_, ext)
                    if image is None:
                        image = audio_waveform_thumb(filepath_, ext, scaled_size, dpi_scale)
                        is_savable_type = False
                        if image is not None:
                            image = self._apply_overlay_color(image, UiColor.GREEN, theme)
                # Blender ======================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.BLENDER_TYPES, mime_fallback=True
                ):
                    image = blender_thumb(filepath_)
                # PDF ==========================================================
                elif MediaCategories.is_ext_in_category(
                    ext, MediaCategories.PDF_TYPES, mime_fallback=True
                ):
                    image = pdf_thumb(filepath_, scaled_size, ext)
                # Archives =====================================================
                elif MediaCategories.is_ext_in_category(ext, MediaCategories.ARCHIVE_TYPES):
                    image = archive_thumb(filepath_, ext=ext)
                # MDIPACK ======================================================
                elif MediaCategories.is_ext_in_category(ext, MediaCategories.MDIPACK_TYPES):
                    image = medibang_paint_thumb(filepath_)
                # Paint.NET ====================================================
                elif MediaCategories.is_ext_in_category(ext, MediaCategories.PAINT_DOT_NET_TYPES):
                    image = paint_dot_net_thumb(filepath_)
                # No Rendered Thumbnail ========================================
                if not image:
                    raise NoRendererError

                if image:
                    image = self._resize_image(image, (scaled_size, scaled_size))

                if cache_filename and is_savable_type and image and cache:
                    cache.save_image(image, cache_filename, mode="RGBA")

            except (
                AssertionError,
                ChildProcessError,
                DecompressionBombError,
                UnidentifiedImageError,
                ValueError,
            ) as e:
                logger.error(
                    "[FileRenderer] Couldn't render thumbnail",
                    filepath=filepath,
                    error=type(e).__name__,
                )
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
