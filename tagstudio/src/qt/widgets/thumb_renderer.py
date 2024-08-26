# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import logging
import math
from pathlib import Path

import cv2
import rawpy
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
from PIL.Image import DecompressionBombError
from PySide6.QtCore import QObject, Signal, QSize
from PySide6.QtGui import QPixmap
from src.qt.helpers.gradient import four_corner_gradient_background
from src.qt.helpers.text_wrapper import wrap_full_text
from src.core.constants import FONT_SAMPLE_SIZES, FONT_SAMPLE_TEXT
from src.core.media_types import MediaType, MediaCategories
from src.core.utils.encoding import detect_char_encoding
from src.qt.helpers.blender_thumbnailer import blend_thumb

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

        adj_size = math.ceil(max(base_size[0], base_size[1]) * pixel_ratio)
        if is_loading:
            final = ThumbRenderer.thumb_loading_512.resize(
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

                    # Normal Images --------------------------------------------
                    else:
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

                # Videos =======================================================
                elif MediaType.VIDEO in MediaCategories.get_types(ext, True):
                    video = cv2.VideoCapture(str(_filepath))
                    frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)
                    if frame_count <= 0:
                        raise cv2.error("File is invalid or has 0 frames")
                    video.set(cv2.CAP_PROP_POS_FRAMES, frame_count // 2)
                    success, frame = video.read()
                    if not success:
                        # Depending on the video format, compression, and frame
                        # count, seeking halfway does not work and the thumb
                        # must be pulled from the earliest available frame.
                        video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        success, frame = video.read()
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image = Image.fromarray(frame)

                # Plain Text ===================================================
                elif MediaType.PLAINTEXT in MediaCategories.get_types(ext):
                    encoding = detect_char_encoding(_filepath)
                    with open(_filepath, "r", encoding=encoding) as text_file:
                        text = text_file.read(256)
                    bg = Image.new("RGB", (256, 256), color="#1e1e1e")
                    draw = ImageDraw.Draw(bg)
                    draw.text((16, 16), text, fill=(255, 255, 255))
                    image = bg
                # Fonts ========================================================
                elif MediaType.FONT in MediaCategories.get_types(ext, True):
                    # Scale the sample font sizes to the preview image
                    # resolution,assuming the sizes are tuned for 256px.
                    scaled_sizes: list[int] = [
                        math.floor(x * (adj_size / 256)) for x in FONT_SAMPLE_SIZES
                    ]
                    if gradient:
                        # handles small thumbnails
                        bg = Image.new("RGB", (adj_size, adj_size), color="#1e1e1e")
                        draw = ImageDraw.Draw(bg)
                        font = ImageFont.truetype(
                            _filepath, size=math.ceil(adj_size * 0.65)
                        )
                        draw.text((10, 0), "Aa", font=font)
                    else:
                        # handles big thumbnails and renders a sample text in multiple font sizes
                        bg = Image.new("RGB", (adj_size, adj_size), color="#1e1e1e")
                        draw = ImageDraw.Draw(bg)
                        lines_of_padding = 2
                        y_offset = 0

                        for font_size in scaled_sizes:
                            font = ImageFont.truetype(_filepath, size=font_size)
                            text_wrapped: str = wrap_full_text(
                                FONT_SAMPLE_TEXT, font=font, width=adj_size, draw=draw
                            )
                            draw.multiline_text((0, y_offset), text_wrapped, font=font)
                            y_offset += (
                                len(text_wrapped.split("\n")) + lines_of_padding
                            ) * draw.textbbox((0, 0), "A", font=font)[-1]

                    image = bg
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
                elif MediaType.BLENDER in MediaCategories.get_types(ext):
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
                OSError,
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
