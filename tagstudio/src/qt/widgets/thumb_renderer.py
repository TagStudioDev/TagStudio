# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import logging
import math
from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
import rawpy
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
from pydub import AudioSegment, exceptions
from PySide6.QtCore import QObject, QSize, Qt, Signal
from PySide6.QtGui import QGuiApplication, QPixmap
from src.core.constants import FONT_SAMPLE_SIZES, FONT_SAMPLE_TEXT
from src.core.media_types import MediaCategories, MediaType
from src.core.palette import ColorType, get_ui_color
from src.core.utils.encoding import detect_char_encoding
from src.qt.helpers.blender_thumbnailer import blend_thumb
from src.qt.helpers.color_overlay import theme_fg_overlay
from src.qt.helpers.file_tester import is_readable_video
from src.qt.helpers.gradient import four_corner_gradient
from src.qt.helpers.text_wrapper import wrap_full_text
from src.qt.resource_manager import ResourceManager

ImageFile.LOAD_TRUNCATED_IMAGES = True

logging.basicConfig(format="%(message)s", level=logging.INFO)
register_heif_opener()
register_avif_opener()


class ThumbRenderer(QObject):
    """A class for rendering image and file thumbnails."""

    rm: ResourceManager = ResourceManager()
    updated = Signal(float, QPixmap, QSize, str)
    updated_ratio = Signal(float)

    thumb_loading_512: Image.Image = Image.open(
        Path(__file__).parents[3] / "resources/qt/images/thumb_loading_512.png"
    )
    thumb_loading_512.load()

    # TODO: Make dynamic font sized given different pixel ratios
    font_pixel_ratio: float = 1
    ext_font = ImageFont.truetype(
        Path(__file__).parents[3] / "resources/qt/fonts/Oxanium-Bold.ttf",
        math.floor(12 * font_pixel_ratio),
    )

    def __init__(self) -> None:
        super().__init__()

        # Cached thumbnail elements.
        # Key: Size + Pixel Ratio Tuple (Ex. (512, 512, 1.25))
        self.thumb_masks: dict = {}
        self.raised_edges: dict = {}

        # Key: ("name", "color", 512, 512, 1.25)
        self.icons: dict = {}

    def _get_resource_id(self, url: Path) -> str:
        """Return the name of the icon resource to use for a file type.
        Special terms will return special resources.

        Args:
            url (Path): The file url to assess. "$LOADING" will return the loading graphic.
        """
        ext = url.suffix.lower()
        types: set[MediaType] = MediaCategories.get_types(ext, True)

        # Loop though the specific (non-IANA) categories and return the string
        # name of the first matching category found.
        for cat in MediaCategories.ALL_CATEGORIES:
            if not cat.is_iana:
                if cat.media_type in types:
                    return cat.media_type.value

        # If the type is broader (IANA registered) then search those types.
        for cat in MediaCategories.ALL_CATEGORIES:
            if cat.is_iana:
                if cat.media_type in types:
                    return cat.media_type.value

        return "file_generic"

    def _get_mask(self, size: tuple[int, int], pixel_ratio: float) -> Image.Image:
        """
        Returns a thumbnail mask given a size and pixel ratio.
        If one is not already cached, then a new one will be rendered.
        """
        item: Image.Image = self.thumb_masks.get((*size, pixel_ratio))
        if not item:
            item = self._render_mask(size, pixel_ratio)
            self.thumb_masks[(*size, pixel_ratio)] = item
        return item

    def _get_edge(
        self, size: tuple[int, int], pixel_ratio: float
    ) -> tuple[Image.Image, Image.Image]:
        """
        Returns a thumbnail raised edge graphic given a size and pixel ratio.
        If one is not already cached, then a new one will be rendered.
        """
        logging.info((*size, pixel_ratio))
        item: tuple[Image.Image, Image.Image] = self.raised_edges.get(
            (*size, pixel_ratio)
        )
        if not item:
            item = self._render_edge(size, pixel_ratio)
            self.raised_edges[(*size, pixel_ratio)] = item
        else:
            logging.info("using cached edge")
        return item

    def _get_icon(
        self, name: str, color: str, size: tuple[int, int], pixel_ratio: float = 1.0
    ) -> Image.Image:
        """Retrieves a new or cached icon.

        Args:
            name (str): The name of the icon resource.
            color (str): The color to use for the icon.
            size (tuple[int,int]): The size of the icon.
            pixel_ratio (float): The screen pixel ratio.
        """
        item: Image.Image = self.icons.get((name, color, *size, pixel_ratio))
        if not item:
            item = self._render_icon(name, color, size, pixel_ratio)
            self.raised_edges[(name, *color, size, pixel_ratio)] = item
        return item

    def _render_mask(self, size: tuple[int, int], pixel_ratio) -> Image.Image:
        """Renders a thumbnail mask."""
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
            radius=math.ceil(radius_factor * smooth_factor * pixel_ratio),
            fill="white",
        )
        im = im.resize(
            size,
            resample=Image.Resampling.BILINEAR,
        )
        return im

    def _render_edge(
        self, size: tuple[int, int], pixel_ratio
    ) -> tuple[Image.Image, Image.Image]:
        """Renders a thumbnail highlight border."""
        logging.info("rendering edge")
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
            radius=math.ceil(
                (radius_factor * smooth_factor * pixel_ratio) - (pixel_ratio * 3)
            ),
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
        # sh_bg = sh_bg.resize(
        #     size,
        #     resample=Image.Resampling.BILINEAR,
        # )

        # Shadow
        # sh_bg: Image.Image = Image.new(
        #     mode="RGBA",
        #     size=tuple([d * smooth_factor for d in size]),  # type: ignore
        #     color="black",
        # )
        # sh_inner_mask: Image.Image = Image.new(
        #     mode="RGBA",
        #     size=tuple([d * smooth_factor for d in size]),  # type: ignore
        #     color="red",
        # )
        # draw = ImageDraw.Draw(sh_inner_mask)
        # draw.rounded_rectangle(
        #     (0, 0) + tuple([d - 1 for d in sh_bg.size]),
        #     radius=math.ceil(radius_factor * smooth_factor * pixel_ratio),
        #     fill="black",
        #     outline="red",
        #     width=width,
        # )
        # sh_bg.putalpha(sh_inner_mask.getchannel(0))
        # # sh_bg = sh_bg.resize(
        # #     size,
        # #     resample=Image.Resampling.BILINEAR,
        # # )

        # alpha_mask: Image.Image = self._get_mask(sh_bg.size, pixel_ratio)
        # im_sh = Image.new("RGBA", sh_bg.size, "#00000000")
        # im_sh.paste(sh_bg, mask=alpha_mask.getchannel(0))

        # im_sh = im_sh.resize(
        #     size,
        #     resample=Image.Resampling.BILINEAR,
        # )

        return (im_hl, im_sh)

    def _render_icon(
        self, name: str, color: str, size: tuple[int, int], pixel_ratio: float
    ) -> Image.Image:
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
        draw = ImageDraw.Draw(im)
        draw.rounded_rectangle(
            (0, 0) + tuple([d - 1 for d in im.size]),
            radius=math.ceil(radius_factor * smooth_factor * pixel_ratio),
            fill="black",
            outline="#FF0000",
            width=math.floor(pixel_ratio * 8),
        )

        # Resize image to final size
        im = im.resize(
            size,
            resample=Image.Resampling.BILINEAR,
        )
        fg: Image.Image = Image.new("RGB", size=size, color="#00FF00")

        # Get icon by name
        icon: Image.Image = self.rm.get(name)
        if not icon:
            icon = self.rm.get("file_generic")
            if not icon:
                icon = Image.new(mode="RGBA", size=(32, 32), color="magenta")

        # Resize icon to fit icon_ratio
        icon = icon.resize(
            (math.ceil(size[0] // icon_ratio), math.ceil(size[1] // icon_ratio))
        )

        # Paste icon centered
        im.paste(
            im=fg.resize(
                (math.ceil(size[0] // icon_ratio), math.ceil(size[1] // icon_ratio))
            ),
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

    def _apply_overlay_color(self, image: Image.Image, color: str) -> Image.Image:
        """Apply a gradient effect over an an image.
        Red channel for foreground, green channel for outline, none for background."""
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
            else "#FFFFFF"
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

    def _apply_edge(self, image: Image.Image, edge: tuple[Image.Image, Image.Image]):
        """Apply a given edge effect to an image.

        Args:
            image (Image.Image): The image to apply the edge to.
            edge (Image.Image): The edge image to apply.
        """
        logging.info("applying edge")
        im: Image.Image = image
        im_hl, im_sh = edge

        # Configure and apply a soft light overlay.
        # This makes up the bulk of the effect.
        # edge_soft = im_hl.copy()
        im_hl.putalpha(ImageEnhance.Brightness(im_hl.getchannel(3)).enhance(0.75))
        im.paste(ImageChops.soft_light(im, im_hl), mask=im_hl.getchannel(3))

        # Configure and apply a hard light overlay.
        # This helps with contrast.
        # edge_hard = im_sh.copy()
        # edge_hard.putalpha(ImageEnhance.Brightness(im_sh.getchannel(3)).enhance(0.75))
        im_sh.putalpha(ImageEnhance.Brightness(im_sh.getchannel(3)).enhance(0.75))
        im.paste(im_sh, mask=im_sh.getchannel(3))
        # im.paste(edge_hard, mask=im_sh.getchannel(3))

        return im

    def _audio_album_thumb(self, filepath: Path, ext: str) -> Image.Image | None:
        """Gets an album cover from an audio file if one is present."""
        image: Image.Image = None
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
            logging.error(
                f"[ThumbRenderer][ERROR]: Couldn't read album artwork for {filepath.name} ({type(e).__name__})"
            )
        return image

    def _audio_waveform_thumb(
        self, filepath: Path, ext: str, size: int, pixel_ratio: float
    ) -> Image.Image | None:
        """Render a waveform image from an audio file."""
        # BASE_SCALE used for drawing on a larger image and resampling down
        # to provide an antialiased effect.
        BASE_SCALE: int = 2
        size_scaled: int = size * BASE_SCALE
        ALLOW_SMALL_MIN: bool = False
        SAMPLES_PER_BAR: int = 3
        im: Image.Image = None

        try:
            BARS: int = min(math.floor((size // pixel_ratio) / 5), 64)
            audio: AudioSegment = AudioSegment.from_file(filepath, ext[1:])
            data = np.fromstring(audio._data, np.int16)  # type: ignore
            data_indices = np.linspace(1, len(data), num=BARS * SAMPLES_PER_BAR)

            BAR_MARGIN: float = ((size_scaled / (BARS * 3)) * BASE_SCALE) / 2
            LINE_WIDTH: float = ((size_scaled - BAR_MARGIN) / (BARS * 3)) * BASE_SCALE
            BAR_HEIGHT: float = (size_scaled) - (size_scaled // BAR_MARGIN)

            count: int = 0
            maximum_item: int = 0
            max_array: list = []
            highest_line: int = 0

            for i in range(-1, len(data_indices)):
                d = data[math.ceil(data_indices[i]) - 1]
                if count < SAMPLES_PER_BAR:
                    count = count + 1
                    if abs(d) > maximum_item:
                        maximum_item = abs(d)
                else:
                    max_array.append(maximum_item)

                    if maximum_item > highest_line:
                        highest_line = maximum_item

                    maximum_item = 0
                    count = 1

            line_ratio = max(highest_line / BAR_HEIGHT, 1)

            im = Image.new("RGB", (size_scaled, size_scaled), color="#000000")
            draw = ImageDraw.Draw(im)

            current_x = BAR_MARGIN
            for item in max_array:
                item_height = item / line_ratio

                # If small minimums are not allowed, raise all values
                # smaller than the line width to the same value.
                if not ALLOW_SMALL_MIN:
                    item_height = max(item_height, LINE_WIDTH)

                current_y = (
                    BAR_HEIGHT - item_height + (size_scaled // BAR_MARGIN)
                ) // 2

                draw.rounded_rectangle(
                    (
                        current_x,
                        current_y,
                        (current_x + LINE_WIDTH),
                        (current_y + item_height),
                    ),
                    radius=100 * BASE_SCALE,
                    fill=("#FF0000"),
                    outline=("#FFFF00"),
                    width=max(math.ceil(LINE_WIDTH / 6), BASE_SCALE),
                )

                current_x = current_x + LINE_WIDTH + BAR_MARGIN

            im.resize((size, size), Image.Resampling.BILINEAR)

        except exceptions.CouldntDecodeError as e:
            logging.error(
                f"[ThumbRenderer][WAVEFORM][ERROR]: Couldn't render waveform for {filepath.name} ({type(e).__name__})"
            )
        return im

    def _blender(self, filepath: Path) -> Image.Image:
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
            FileNotFoundError,
            TypeError,
        ) as e:
            if str(e) == "expected string or buffer":
                logging.info(
                    f"[ThumbRenderer][BLENDER][INFO] {filepath.name} Doesn't have an embedded thumbnail. ({type(e).__name__})"
                )

            else:
                logging.error(
                    f"[ThumbRenderer][BLENDER][ERROR]: Couldn't render thumbnail for {filepath.name} ({type(e).__name__})"
                )
        return im

    def _font_short_thumb(self, filepath: Path, size: int) -> Image.Image:
        """Render a small font preview ("Aa") thumbnail from a font file."""
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
            im = self._apply_overlay_color(bg, "purple")
        except OSError as e:
            logging.info(
                f"[ThumbRenderer][FONT][ERROR] Couldn't Render thumbnail for font {filepath.name} ({type(e).__name__})"
            )
        return im

    def _font_long_thumb(self, filepath: Path, size: int) -> Image.Image:
        """Render a large font preview ("Alphabet") thumbnail from a font file."""
        # Scale the sample font sizes to the preview image
        # resolution,assuming the sizes are tuned for 256px.
        im: Image.Image = None
        try:
            scaled_sizes: list[int] = [
                math.floor(x * (size / 256)) for x in FONT_SAMPLE_SIZES
            ]
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
                y_offset += (
                    len(text_wrapped.split("\n")) + lines_of_padding
                ) * draw.textbbox((0, 0), "A", font=font)[-1]
            im = theme_fg_overlay(bg, use_alpha=False)
        except OSError as e:
            logging.info(
                f"[ThumbRenderer][FONT][ERROR] Couldn't Render thumbnail for font {filepath.name} ({type(e).__name__})"
            )
        return im

    def _image_raw_thumb(self, filepath: Path) -> Image.Image:
        im: Image.Image = None
        try:
            with rawpy.imread(str(filepath)) as raw:
                rgb = raw.postprocess()
                im = Image.frombytes(
                    "RGB",
                    (rgb.shape[1], rgb.shape[0]),
                    rgb,
                    decoder_name="raw",
                )
        except DecompressionBombError as e:
            logging.info(
                f"[ThumbRenderer][RAW][WARNING] Couldn't Render thumbnail for {filepath.name} ({type(e).__name__})"
            )
        except (
            rawpy._rawpy.LibRawIOError,
            rawpy._rawpy.LibRawFileUnsupportedError,
        ) as e:
            logging.info(
                f"[ThumbRenderer][RAW][ERROR] Couldn't Render thumbnail for raw image {filepath.name} ({type(e).__name__})"
            )
        return im

    def _image_thumb(self, filepath: Path) -> Image.Image:
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
        ) as e:
            logging.error(
                f"[ThumbRenderer][IMAGE][ERROR]: Couldn't render thumbnail for {filepath.name} ({type(e).__name__})"
            )
        return im

    def _image_vector_thumb(self, filepath: Path, size: int) -> Image.Image:
        # TODO: Implement.
        im: Image.Image = None
        return im

    def _model_stl_thumb(self, filepath: Path, size: int) -> Image.Image:
        # TODO: Implement.
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

    def _text_thumb(self, filepath: Path, size: int) -> Image.Image:
        im: Image.Image = None

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
            with open(filepath, "r", encoding=encoding) as text_file:
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
            logging.info(
                f"[ThumbRenderer][TEXT][ERROR]: Couldn't render thumbnail for {filepath.name} ({type(e).__name__})"
            )
        return im

    def _video_thumb(self, filepath: Path) -> Image.Image:
        im: Image.Image = None
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
                success, frame = video.read()
                if not success:
                    # Depending on the video format, compression, and frame
                    # count, seeking halfway does not work and the thumb
                    # must be pulled from the earliest available frame.
                    video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                im = Image.fromarray(frame)
            # else:
            #     im = self._get_icon(
            #         name="file_generic",
            #         color="red",
            #         size=(size, size),
            #         pixel_ratio=pixel_ratio,
            #     )
        except (
            UnidentifiedImageError,
            cv2.error,
            DecompressionBombError,
            OSError,
        ) as e:
            logging.error(
                f"[ThumbRenderer][ERROR]: Couldn't render thumbnail for {filepath.name} ({type(e).__name__})"
            )
        return im

    def render(
        self,
        timestamp: float,
        filepath: str | Path,
        base_size: tuple[int, int],
        pixel_ratio: float,
        is_loading=False,
        gradient=False,
        update_on_ratio_change=False,
    ):
        """Internal renderer. Renders an entry/element thumbnail for the GUI."""
        loading_thumb: Image.Image = ThumbRenderer.thumb_loading_512

        image: Image.Image = None
        pixmap: QPixmap = None
        final: Image.Image = None
        _filepath: Path = Path(filepath)
        resampling_method = Image.Resampling.BILINEAR

        if ThumbRenderer.font_pixel_ratio != pixel_ratio:
            ThumbRenderer.font_pixel_ratio = pixel_ratio
            ThumbRenderer.ext_font = ImageFont.truetype(
                Path(__file__).parents[3] / "resources/qt/fonts/Oxanium-Bold.ttf",
                math.floor(12 * ThumbRenderer.font_pixel_ratio),
            )

        if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Light:
            loading_thumb = theme_fg_overlay(loading_thumb)

        adj_size = math.ceil(max(base_size[0], base_size[1]) * pixel_ratio)
        if is_loading:
            final = loading_thumb.resize(
                (adj_size, adj_size), resample=Image.Resampling.BILINEAR
            )
            qim = ImageQt.ImageQt(final)
            pixmap = QPixmap.fromImage(qim)
            pixmap.setDevicePixelRatio(pixel_ratio)
            if update_on_ratio_change:
                self.updated_ratio.emit(1)
        elif _filepath:
            try:
                ext: str = _filepath.suffix.lower()
                # Images =======================================================
                if MediaType.IMAGE in MediaCategories.get_types(ext, True):
                    # Raw Images -----------------------------------------------
                    if MediaType.IMAGE_RAW in MediaCategories.get_types(ext, True):
                        image = self._image_raw_thumb(_filepath)
                    elif MediaType.IMAGE_VECTOR in MediaCategories.get_types(ext, True):
                        image = self._image_vector_thumb(_filepath, adj_size)
                    # Normal Images --------------------------------------------
                    else:
                        image = self._image_thumb(_filepath)
                # Videos =======================================================
                elif MediaType.VIDEO in MediaCategories.get_types(ext, True):
                    image = self._video_thumb(_filepath)
                # Plain Text ===================================================
                elif MediaType.PLAINTEXT in MediaCategories.get_types(ext):
                    image = self._text_thumb(_filepath, adj_size)
                # Fonts ========================================================
                elif MediaType.FONT in MediaCategories.get_types(ext, True):
                    if gradient:
                        # Short (Aa) Preview
                        image = self._font_short_thumb(_filepath, adj_size)
                    else:
                        # Large (Full Alphabet) Preview
                        image = self._font_long_thumb(_filepath, adj_size)
                # Audio ========================================================
                elif MediaType.AUDIO in MediaCategories.get_types(ext, True):
                    image = self._audio_album_thumb(_filepath, ext)
                    if image is None:
                        image = self._audio_waveform_thumb(
                            _filepath, ext, adj_size, pixel_ratio
                        )
                        if image is not None:
                            image = self._apply_overlay_color(image, "green")

                # Blender ===========================================================
                elif MediaType.BLENDER in MediaCategories.get_types(ext):
                    image = self._blender(_filepath)

                # No Rendered Thumbnail ========================================
                if not image:
                    raise UnidentifiedImageError

                orig_x, orig_y = image.size
                new_x, new_y = (adj_size, adj_size)

                if orig_x > orig_y:
                    new_x = adj_size
                    new_y = math.ceil(adj_size * (orig_y / orig_x))
                elif orig_y > orig_x:
                    new_y = adj_size
                    new_x = math.ceil(adj_size * (orig_x / orig_y))

                if update_on_ratio_change:
                    self.updated_ratio.emit(new_x / new_y)

                resampling_method = (
                    Image.Resampling.NEAREST
                    if max(image.size[0], image.size[1])
                    < max(base_size[0], base_size[1])
                    else Image.Resampling.BILINEAR
                )
                image = image.resize((new_x, new_y), resample=resampling_method)
                if gradient:
                    mask: Image.Image = self._get_mask(
                        (adj_size, adj_size), pixel_ratio
                    )
                    edge: tuple[Image.Image, Image.Image] = self._get_edge(
                        (adj_size, adj_size), pixel_ratio
                    )
                    final = self._apply_edge(
                        four_corner_gradient(image, (adj_size, adj_size), mask),
                        edge,
                    )
                else:
                    scalar = 4
                    mask: Image.Image = self._get_mask(image.size, pixel_ratio)
                    # rec: Image.Image = Image.new(
                    #     "RGB",
                    #     tuple([d * scalar for d in image.size]),  # type: ignore
                    #     "black",
                    # )
                    # draw = ImageDraw.Draw(rec)
                    # draw.rounded_rectangle(
                    #     (0, 0) + tuple([d - 1 for d in rec.size]),
                    #     (base_size[0] // 32) * scalar * pixel_ratio,
                    #     fill="red",
                    # )
                    # rec = rec.resize(
                    #     tuple([d // scalar for d in rec.size]),
                    #     resample=Image.Resampling.BILINEAR,
                    # )
                    final = Image.new("RGBA", image.size, (0, 0, 0, 0))
                    final.paste(image, mask=mask.getchannel(0))

            except FileNotFoundError as e:
                logging.info(
                    f"[ThumbRenderer][ERROR]: Couldn't render thumbnail for {_filepath.name} ({type(e).__name__})"
                )
                if update_on_ratio_change:
                    self.updated_ratio.emit(1)
                final = self._get_icon(
                    name="broken_link_icon",
                    color="red",
                    size=(adj_size, adj_size),
                    pixel_ratio=pixel_ratio,
                )
            except (
                UnidentifiedImageError,
                DecompressionBombError,
            ) as e:
                logging.info(
                    f"[ThumbRenderer][ERROR]: Couldn't render thumbnail for {_filepath.name} ({type(e).__name__})"
                )

                if update_on_ratio_change:
                    self.updated_ratio.emit(1)
                final = self._get_icon(
                    name=self._get_resource_id(_filepath),
                    # name="file_generic",
                    color="",
                    size=(adj_size, adj_size),
                    pixel_ratio=pixel_ratio,
                )
            qim = ImageQt.ImageQt(final)
            if image:
                image.close()
            pixmap = QPixmap.fromImage(qim)
            pixmap.setDevicePixelRatio(pixel_ratio)

        if pixmap:
            self.updated.emit(
                timestamp,
                pixmap,
                QSize(
                    math.ceil(adj_size / pixel_ratio),
                    math.ceil(final.size[1] / pixel_ratio),
                ),
                _filepath.suffix.lower(),
            )

        else:
            self.updated.emit(
                timestamp, QPixmap(), QSize(*base_size), _filepath.suffix.lower()
            )
