# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import logging
import math
import cv2
import rawpy
import numpy as np
from pillow_heif import register_heif_opener, register_avif_opener
from PIL import (
    Image,
    UnidentifiedImageError,
    ImageQt,
    ImageDraw,
    ImageFont,
    ImageOps,
    ImageFile,
)
from io import BytesIO
from pathlib import Path
from PIL.Image import DecompressionBombError
from pydub import AudioSegment, exceptions
from mutagen import id3, flac, mp4
from PySide6.QtCore import Qt, QObject, Signal, QSize
from PySide6.QtGui import QGuiApplication, QPixmap
from src.qt.helpers.color_overlay import theme_fg_overlay
from src.qt.helpers.gradient import four_corner_gradient_background
from src.qt.helpers.text_wrapper import wrap_full_text
from src.core.constants import (
    AUDIO_TYPES,
    PLAINTEXT_TYPES,
    FONT_TYPES,
    VIDEO_TYPES,
    IMAGE_TYPES,
    RAW_IMAGE_TYPES,
    FONT_SAMPLE_TEXT,
    FONT_SAMPLE_SIZES,
    BLENDER_TYPES,
)
from src.core.utils.encoding import detect_char_encoding
from src.core.palette import ColorType, get_ui_color
from src.qt.helpers.blender_thumbnailer import blend_thumb
from src.qt.helpers.file_tester import is_readable_video

ImageFile.LOAD_TRUNCATED_IMAGES = True

ERROR = "[ERROR]"
WARNING = "[WARNING]"
INFO = "[INFO]"

logging.basicConfig(format="%(message)s", level=logging.INFO)
register_heif_opener()
register_avif_opener()


class ThumbRenderer(QObject):
    # finished = Signal()
    updated = Signal(float, QPixmap, QSize, str)
    updated_ratio = Signal(float)
    # updatedImage = Signal(QPixmap)
    # updatedSize = Signal(QSize)

    thumb_mask_512: Image.Image = Image.open(
        Path(__file__).parents[3] / "resources/qt/images/thumb_mask_512.png"
    )
    thumb_mask_512.load()

    thumb_mask_hl_512: Image.Image = Image.open(
        Path(__file__).parents[3] / "resources/qt/images/thumb_mask_hl_512.png"
    )
    thumb_mask_hl_512.load()

    thumb_loading_512: Image.Image = Image.open(
        Path(__file__).parents[3] / "resources/qt/images/thumb_loading_512.png"
    )
    thumb_loading_512.load()

    thumb_broken_512: Image.Image = Image.open(
        Path(__file__).parents[3] / "resources/qt/images/thumb_broken_512.png"
    )
    thumb_broken_512.load()

    thumb_file_default_512: Image.Image = Image.open(
        Path(__file__).parents[3] / "resources/qt/images/thumb_file_default_512.png"
    )
    thumb_file_default_512.load()

    # thumb_debug: Image.Image = Image.open(Path(
    # 	f'{Path(__file__).parents[2]}/resources/qt/images/temp.jpg'))
    # thumb_debug.load()

    # TODO: Make dynamic font sized given different pixel ratios
    font_pixel_ratio: float = 1
    ext_font = ImageFont.truetype(
        Path(__file__).parents[3] / "resources/qt/fonts/Oxanium-Bold.ttf",
        math.floor(12 * font_pixel_ratio),
    )

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
                ext = _filepath.suffix.lower()
                # Images =======================================================
                if ext in IMAGE_TYPES:
                    try:
                        image = Image.open(_filepath)
                        if image.mode != "RGB" and image.mode != "RGBA":
                            image = image.convert(mode="RGBA")
                        if image.mode == "RGBA":
                            new_bg = Image.new("RGB", image.size, color="#1e1e1e")
                            new_bg.paste(image, mask=image.getchannel(3))
                            image = new_bg

                        image = ImageOps.exif_transpose(image)
                    except DecompressionBombError as e:
                        logging.info(
                            f"[ThumbRenderer]{WARNING} Couldn't Render thumbnail for {_filepath.name} ({type(e).__name__})"
                        )

                elif ext in RAW_IMAGE_TYPES:
                    try:
                        with rawpy.imread(str(_filepath)) as raw:
                            rgb = raw.postprocess()
                            image = Image.frombytes(
                                "RGB",
                                (rgb.shape[1], rgb.shape[0]),
                                rgb,
                                decoder_name="raw",
                            )
                    except DecompressionBombError as e:
                        logging.info(
                            f"[ThumbRenderer]{WARNING} Couldn't Render thumbnail for {_filepath.name} ({type(e).__name__})"
                        )
                    except (
                        rawpy._rawpy.LibRawIOError,
                        rawpy._rawpy.LibRawFileUnsupportedError,
                    ) as e:
                        logging.info(
                            f"[ThumbRenderer]{ERROR} Couldn't Render thumbnail for raw image {_filepath.name} ({type(e).__name__})"
                        )

                # Videos =======================================================
                elif ext in VIDEO_TYPES:
                    if is_readable_video(_filepath):
                        video = cv2.VideoCapture(str(_filepath), cv2.CAP_FFMPEG)
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
                            success, frame = video.read()
                            if not success:
                                # Depending on the video format, compression, and frame
                                # count, seeking halfway does not work and the thumb
                                # must be pulled from the earliest available frame.
                                video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                                success, frame = video.read()
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        image = Image.fromarray(frame)
                    else:
                        image = self.thumb_file_default_512

                # Plain Text ===================================================
                elif ext in PLAINTEXT_TYPES:
                    bg_color: str = (
                        "#1E1E1E"
                        if QGuiApplication.styleHints().colorScheme()
                        is Qt.ColorScheme.Dark
                        else "#FFFFFF"
                    )
                    fg_color: str = (
                        "#FFFFFF"
                        if QGuiApplication.styleHints().colorScheme()
                        is Qt.ColorScheme.Dark
                        else "#111111"
                    )
                    encoding = detect_char_encoding(_filepath)
                    with open(_filepath, "r", encoding=encoding) as text_file:
                        text = text_file.read(256)
                    bg = Image.new("RGB", (256, 256), color=bg_color)
                    draw = ImageDraw.Draw(bg)
                    draw.text((16, 16), text, fill=fg_color)
                    image = bg
                # Fonts ========================================================
                elif _filepath.suffix.lower() in FONT_TYPES:
                    if gradient:
                        # Handles small thumbnails
                        image = self._font_preview_short(_filepath, adj_size)
                    else:
                        # Handles big thumbnails and renders a sample text in multiple font sizes.
                        image = self._font_preview_long(_filepath, adj_size)
                # Audio ========================================================
                elif ext in AUDIO_TYPES:
                    image = self._album_artwork(_filepath, ext)
                    if image is None:
                        image = self._audio_waveform(
                            _filepath, ext, adj_size, pixel_ratio
                        )
                        if image is not None:
                            image = self._apply_overlay_color(image, "green")

                # 3D ===========================================================
                # elif extension == 'stl':
                # 	# Create a new plot
                # 	matplotlib.use('agg')
                # 	figure = plt.figure()
                # 	axes = figure.add_subplot(projection='3d')

                # 	# Load the STL files and add the vectors to the plot
                # 	your_mesh = mesh.Mesh.from_file(_filepath)

                # 	poly_collection = mplot3d.art3d.Poly3DCollection(your_mesh.vectors)
                # 	poly_collection.set_color((0,0,1))  # play with color
                # 	scale = your_mesh.points.flatten()
                # 	axes.auto_scale_xyz(scale, scale, scale)
                # 	axes.add_collection3d(poly_collection)
                # 	# plt.show()
                # 	img_buf = io.BytesIO()
                # 	plt.savefig(img_buf, format='png')
                # 	image = Image.open(img_buf)

                # Blender ===========================================================
                elif _filepath.suffix.lower() in BLENDER_TYPES:
                    try:
                        blend_image = blend_thumb(str(_filepath))

                        bg = Image.new("RGB", blend_image.size, color="#1e1e1e")
                        bg.paste(blend_image, mask=blend_image.getchannel(3))
                        image = bg

                    except (
                        AttributeError,
                        UnidentifiedImageError,
                        FileNotFoundError,
                        TypeError,
                    ) as e:
                        if str(e) == "expected string or buffer":
                            logging.info(
                                f"[ThumbRenderer]{ERROR} {_filepath.name} Doesn't have thumbnail saved. ({type(e).__name__})"
                            )

                        else:
                            logging.info(
                                f"[ThumbRenderer]{ERROR}: Couldn't render thumbnail for {_filepath.name} ({type(e).__name__})"
                            )

                        image = ThumbRenderer.thumb_file_default_512.resize(
                            (adj_size, adj_size), resample=Image.Resampling.BILINEAR
                        )

                # No Rendered Thumbnail ========================================
                else:
                    image = ThumbRenderer.thumb_file_default_512.resize(
                        (adj_size, adj_size), resample=Image.Resampling.BILINEAR
                    )

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
                    mask: Image.Image = ThumbRenderer.thumb_mask_512.resize(
                        (adj_size, adj_size), resample=Image.Resampling.BILINEAR
                    ).getchannel(3)
                    hl: Image.Image = ThumbRenderer.thumb_mask_hl_512.resize(
                        (adj_size, adj_size), resample=Image.Resampling.BILINEAR
                    )
                    final = four_corner_gradient_background(image, adj_size, mask, hl)
                else:
                    scalar = 4
                    rec: Image.Image = Image.new(
                        "RGB",
                        tuple([d * scalar for d in image.size]),  # type: ignore
                        "black",
                    )
                    draw = ImageDraw.Draw(rec)
                    draw.rounded_rectangle(
                        (0, 0) + rec.size,
                        (base_size[0] // 32) * scalar * pixel_ratio,
                        fill="red",
                    )
                    rec = rec.resize(
                        tuple([d // scalar for d in rec.size]),
                        resample=Image.Resampling.BILINEAR,
                    )
                    final = Image.new("RGBA", image.size, (0, 0, 0, 0))
                    final.paste(image, mask=rec.getchannel(0))
            except (
                UnidentifiedImageError,
                FileNotFoundError,
                cv2.error,
                DecompressionBombError,
                UnicodeDecodeError,
            ) as e:
                if e is not UnicodeDecodeError:
                    logging.info(
                        f"[ThumbRenderer]{ERROR}: Couldn't render thumbnail for {_filepath.name} ({type(e).__name__})"
                    )
                if update_on_ratio_change:
                    self.updated_ratio.emit(1)
                final = ThumbRenderer.thumb_broken_512.resize(
                    (adj_size, adj_size), resample=resampling_method
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

    def _album_artwork(self, filepath: Path, ext: str) -> Image.Image | None:
        """Gets an album cover from an audio file if one is present."""
        image: Image.Image = None
        try:
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
        ) as e:
            logging.error(
                f"[ThumbRenderer]{ERROR}: Couldn't read album artwork for {filepath.name} ({type(e).__name__})"
            )
        return image

    def _audio_waveform(
        self, filepath: Path, ext: str, size: int, pixel_ratio: float
    ) -> Image.Image | None:
        """Renders a waveform image from an audio file."""
        # BASE_SCALE used for drawing on a larger image and resampling down
        # to provide an antialiased effect.
        BASE_SCALE: int = 2
        size_scaled: int = size * BASE_SCALE
        ALLOW_SMALL_MIN: bool = False
        SAMPLES_PER_BAR: int = 3
        image: Image.Image = None

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

            image = Image.new("RGB", (size_scaled, size_scaled), color="#000000")
            draw = ImageDraw.Draw(image)

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

            image.resize((size, size), Image.Resampling.BILINEAR)

        except exceptions.CouldntDecodeError as e:
            logging.error(
                f"[ThumbRenderer]{ERROR}: Couldn't render waveform for {filepath.name} ({type(e).__name__})"
            )
        return image

    def _font_preview_short(self, filepath: Path, size: int) -> Image.Image:
        """Renders a small font preview ("Aa") thumbnail from a font file."""
        bg = Image.new("RGB", (size, size), color="#000000")
        raw = Image.new("RGB", (size * 2, size * 2), color="#000000")
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
        return self._apply_overlay_color(bg, "purple")

    def _font_preview_long(self, filepath: Path, size: int) -> Image.Image:
        """Renders a large font preview ("Alphabet") thumbnail from a font file."""
        # Scale the sample font sizes to the preview image
        # resolution,assuming the sizes are tuned for 256px.
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
        return theme_fg_overlay(bg, use_alpha=False)

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

        bg: Image.Image = Image.new("RGB", image.size, color=bg_color)
        fg: Image.Image = Image.new("RGB", image.size, color=fg_color)
        ol: Image.Image = Image.new("RGB", image.size, color=ol_color)
        bg.paste(fg, (0, 0), mask=image.getchannel(0))
        bg.paste(ol, (0, 0), mask=image.getchannel(1))
        return bg
