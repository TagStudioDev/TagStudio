# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import ctypes
import logging
import math
import os
from pathlib import Path

import cv2
from PIL import (
    Image,
    ImageChops,
    UnidentifiedImageError,
    ImageQt,
    ImageDraw,
    ImageFont,
    ImageEnhance,
    ImageOps,
    ImageFile,
)
from PySide6.QtCore import QObject, Signal, QSize
from PySide6.QtGui import QPixmap
from src.core.ts_core import PLAINTEXT_TYPES, VIDEO_TYPES, IMAGE_TYPES

ImageFile.LOAD_TRUNCATED_IMAGES = True

ERROR = f"[ERROR]"
WARNING = f"[WARNING]"
INFO = f"[INFO]"


logging.basicConfig(format="%(message)s", level=logging.INFO)


class ThumbRenderer(QObject):
    # finished = Signal()
    updated = Signal(float, QPixmap, QSize, str)
    updated_ratio = Signal(float)
    # updatedImage = Signal(QPixmap)
    # updatedSize = Signal(QSize)

    thumb_mask_512: Image.Image = Image.open(
        os.path.normpath(
            f"{Path(__file__).parent.parent.parent.parent}/resources/qt/images/thumb_mask_512.png"
        )
    )
    thumb_mask_512.load()

    thumb_mask_hl_512: Image.Image = Image.open(
        os.path.normpath(
            f"{Path(__file__).parent.parent.parent.parent}/resources/qt/images/thumb_mask_hl_512.png"
        )
    )
    thumb_mask_hl_512.load()

    thumb_loading_512: Image.Image = Image.open(
        os.path.normpath(
            f"{Path(__file__).parent.parent.parent.parent}/resources/qt/images/thumb_loading_512.png"
        )
    )
    thumb_loading_512.load()

    thumb_broken_512: Image.Image = Image.open(
        os.path.normpath(
            f"{Path(__file__).parent.parent.parent.parent}/resources/qt/images/thumb_broken_512.png"
        )
    )
    thumb_broken_512.load()

    thumb_file_default_512: Image.Image = Image.open(
        os.path.normpath(
            f"{Path(__file__).parent.parent.parent.parent}/resources/qt/images/thumb_file_default_512.png"
        )
    )
    thumb_file_default_512.load()

    # thumb_debug: Image.Image = Image.open(os.path.normpath(
    # 	f'{Path(__file__).parent.parent.parent}/resources/qt/images/temp.jpg'))
    # thumb_debug.load()

    # TODO: Make dynamic font sized given different pixel ratios
    font_pixel_ratio: float = 1
    ext_font = ImageFont.truetype(
        os.path.normpath(
            f"{Path(__file__).parent.parent.parent.parent}/resources/qt/fonts/Oxanium-Bold.ttf"
        ),
        math.floor(12 * font_pixel_ratio),
    )

    def render(
        self,
        timestamp: float,
        filepath,
        base_size: tuple[int, int],
        pixelRatio: float,
        isLoading=False,
    ):
        """Renders an entry/element thumbnail for the GUI."""
        adj_size: int = 1
        image = None
        pixmap = None
        final = None
        extension: str = None
        broken_thumb = False
        # adj_font_size = math.floor(12 * pixelRatio)
        if ThumbRenderer.font_pixel_ratio != pixelRatio:
            ThumbRenderer.font_pixel_ratio = pixelRatio
            ThumbRenderer.ext_font = ImageFont.truetype(
                os.path.normpath(
                    f"{Path(__file__).parent.parent.parent.parent}/resources/qt/fonts/Oxanium-Bold.ttf"
                ),
                math.floor(12 * ThumbRenderer.font_pixel_ratio),
            )

        if isLoading or filepath:
            adj_size = math.ceil(base_size[0] * pixelRatio)

        if isLoading:
            li: Image.Image = ThumbRenderer.thumb_loading_512.resize(
                (adj_size, adj_size), resample=Image.Resampling.BILINEAR
            )
            qim = ImageQt.ImageQt(li)
            pixmap = QPixmap.fromImage(qim)
            pixmap.setDevicePixelRatio(pixelRatio)
        elif filepath:
            mask: Image.Image = ThumbRenderer.thumb_mask_512.resize(
                (adj_size, adj_size), resample=Image.Resampling.BILINEAR
            ).getchannel(3)
            hl: Image.Image = ThumbRenderer.thumb_mask_hl_512.resize(
                (adj_size, adj_size), resample=Image.Resampling.BILINEAR
            )

            extension = os.path.splitext(filepath)[1][1:].lower()

            try:
                # Images =======================================================
                if extension in IMAGE_TYPES:
                    image = Image.open(filepath)
                    # image = self.thumb_debug
                    if image.mode == "RGBA":
                        # logging.info(image.getchannel(3).tobytes())
                        new_bg = Image.new("RGB", image.size, color="#1e1e1e")
                        new_bg.paste(image, mask=image.getchannel(3))
                        image = new_bg
                    if image.mode != "RGB":
                        image = image.convert(mode="RGB")

                    image = ImageOps.exif_transpose(image)

                # Videos =======================================================
                elif extension in VIDEO_TYPES:
                    video = cv2.VideoCapture(filepath)
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
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image = Image.fromarray(frame)

                # Plain Text ===================================================
                elif extension in PLAINTEXT_TYPES:
                    try:
                        text: str = extension
                        with open(filepath, "r", encoding="utf-8") as text_file:
                            text = text_file.read(256)
                        bg = Image.new("RGB", (256, 256), color="#1e1e1e")
                        draw = ImageDraw.Draw(bg)
                        draw.text((16, 16), text, file=(255, 255, 255))
                        image = bg
                    except:
                        logging.info(
                            f"[ThumbRenderer][ERROR]: Coulnd't render thumbnail for {filepath}"
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

                # img_ratio = new_x / new_y
                image = image.resize((new_x, new_y), resample=Image.Resampling.BILINEAR)

                if image.size != (adj_size, adj_size):
                    # Old 1 color method.
                    # bg_col = image.copy().resize((1, 1)).getpixel((0,0))
                    # bg = Image.new(mode='RGB',size=(adj_size,adj_size),color=bg_col)
                    # bg.thumbnail((1, 1))
                    # bg = bg.resize((adj_size,adj_size), resample=Image.Resampling.NEAREST)

                    # Small gradient background. Looks decent, and is only a one-liner.
                    # bg = image.copy().resize((2, 2), resample=Image.Resampling.BILINEAR).resize((adj_size,adj_size),resample=Image.Resampling.BILINEAR)

                    # Four-Corner Gradient Background.
                    # Not exactly a one-liner, but it's (subjectively) really cool.
                    tl = image.getpixel((0, 0))
                    tr = image.getpixel(((image.size[0] - 1), 0))
                    bl = image.getpixel((0, (image.size[1] - 1)))
                    br = image.getpixel(((image.size[0] - 1), (image.size[1] - 1)))
                    bg = Image.new(mode="RGB", size=(2, 2))
                    bg.paste(tl, (0, 0, 2, 2))
                    bg.paste(tr, (1, 0, 2, 2))
                    bg.paste(bl, (0, 1, 2, 2))
                    bg.paste(br, (1, 1, 2, 2))
                    bg = bg.resize(
                        (adj_size, adj_size), resample=Image.Resampling.BICUBIC
                    )

                    bg.paste(
                        image,
                        box=(
                            (adj_size - image.size[0]) // 2,
                            (adj_size - image.size[1]) // 2,
                        ),
                    )

                    bg.putalpha(mask)
                    final = bg

                else:
                    image.putalpha(mask)
                    final = image

                hl_soft = hl.copy()
                hl_soft.putalpha(ImageEnhance.Brightness(hl.getchannel(3)).enhance(0.5))
                final.paste(
                    ImageChops.soft_light(final, hl_soft), mask=hl_soft.getchannel(3)
                )

                # hl_add = hl.copy()
                # hl_add.putalpha(ImageEnhance.Brightness(hl.getchannel(3)).enhance(.25))
                # final.paste(hl_add, mask=hl_add.getchannel(3))

            except (UnidentifiedImageError, FileNotFoundError, cv2.error):
                broken_thumb = True
                final = ThumbRenderer.thumb_broken_512.resize(
                    (adj_size, adj_size), resample=Image.Resampling.BILINEAR
                )

            qim = ImageQt.ImageQt(final)
            if image:
                image.close()
            pixmap = QPixmap.fromImage(qim)
            pixmap.setDevicePixelRatio(pixelRatio)

        if pixmap:
            self.updated.emit(timestamp, pixmap, QSize(*base_size), extension)

        else:
            self.updated.emit(timestamp, QPixmap(), QSize(*base_size), extension)

    def render_big(
        self,
        timestamp: float,
        filepath,
        base_size: tuple[int, int],
        pixelRatio: float,
        isLoading=False,
    ):
        """Renders a large, non-square entry/element thumbnail for the GUI."""
        adj_size: int = 1
        image: Image.Image = None
        pixmap: QPixmap = None
        final: Image.Image = None
        extension: str = None
        broken_thumb = False
        img_ratio = 1
        # adj_font_size = math.floor(12 * pixelRatio)
        if ThumbRenderer.font_pixel_ratio != pixelRatio:
            ThumbRenderer.font_pixel_ratio = pixelRatio
            ThumbRenderer.ext_font = ImageFont.truetype(
                os.path.normpath(
                    f"{Path(__file__).parent.parent.parent.parent}/resources/qt/fonts/Oxanium-Bold.ttf"
                ),
                math.floor(12 * ThumbRenderer.font_pixel_ratio),
            )

        if isLoading or filepath:
            adj_size = math.ceil(max(base_size[0], base_size[1]) * pixelRatio)

        if isLoading:
            adj_size = math.ceil((512 * pixelRatio))
            final: Image.Image = ThumbRenderer.thumb_loading_512.resize(
                (adj_size, adj_size), resample=Image.Resampling.BILINEAR
            )
            qim = ImageQt.ImageQt(final)
            pixmap = QPixmap.fromImage(qim)
            pixmap.setDevicePixelRatio(pixelRatio)
            self.updated_ratio.emit(1)

        elif filepath:
            # mask: Image.Image = ThumbRenderer.thumb_mask_512.resize(
            # 	(adj_size, adj_size), resample=Image.Resampling.BILINEAR).getchannel(3)
            # hl: Image.Image = ThumbRenderer.thumb_mask_hl_512.resize(
            # 	(adj_size, adj_size), resample=Image.Resampling.BILINEAR)

            extension = os.path.splitext(filepath)[1][1:].lower()

            try:
                # Images =======================================================
                if extension in IMAGE_TYPES:
                    image = Image.open(filepath)
                    # image = self.thumb_debug
                    if image.mode == "RGBA":
                        # logging.info(image.getchannel(3).tobytes())
                        new_bg = Image.new("RGB", image.size, color="#1e1e1e")
                        new_bg.paste(image, mask=image.getchannel(3))
                        image = new_bg
                    if image.mode != "RGB":
                        image = image.convert(mode="RGB")

                    image = ImageOps.exif_transpose(image)

                # Videos =======================================================
                elif extension in VIDEO_TYPES:
                    video = cv2.VideoCapture(filepath)
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
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image = Image.fromarray(frame)
                # Plain Text ===================================================
                elif extension in PLAINTEXT_TYPES:
                    try:
                        text: str = extension
                        with open(filepath, "r", encoding="utf-8") as text_file:
                            text = text_file.read(256)
                        bg = Image.new("RGB", (256, 256), color="#1e1e1e")
                        draw = ImageDraw.Draw(bg)
                        draw.text((16, 16), text, file=(255, 255, 255))
                        image = bg
                    except:
                        logging.info(
                            f"[ThumbRenderer][ERROR]: Coulnd't render thumbnail for {filepath}"
                        )
                # No Rendered Thumbnail ========================================
                else:
                    image = ThumbRenderer.thumb_file_default_512.resize(
                        (adj_size, adj_size), resample=Image.Resampling.BILINEAR
                    )

                if not image:
                    raise UnidentifiedImageError

                orig_x, orig_y = image.size
                if orig_x < adj_size and orig_y < adj_size:
                    new_x, new_y = (adj_size, adj_size)
                    if orig_x > orig_y:
                        new_x = adj_size
                        new_y = math.ceil(adj_size * (orig_y / orig_x))
                    elif orig_y > orig_x:
                        new_y = adj_size
                        new_x = math.ceil(adj_size * (orig_x / orig_y))
                else:
                    new_x, new_y = (adj_size, adj_size)
                    if orig_x > orig_y:
                        new_x = adj_size
                        new_y = math.ceil(adj_size * (orig_y / orig_x))
                    elif orig_y > orig_x:
                        new_y = adj_size
                        new_x = math.ceil(adj_size * (orig_x / orig_y))

                self.updated_ratio.emit(new_x / new_y)
                image = image.resize((new_x, new_y), resample=Image.Resampling.BILINEAR)

                # image = image.resize(
                # 	(new_x, new_y), resample=Image.Resampling.BILINEAR)

                # if image.size != (adj_size, adj_size):
                # 	# Old 1 color method.
                # 	# bg_col = image.copy().resize((1, 1)).getpixel((0,0))
                # 	# bg = Image.new(mode='RGB',size=(adj_size,adj_size),color=bg_col)
                # 	# bg.thumbnail((1, 1))
                # 	# bg = bg.resize((adj_size,adj_size), resample=Image.Resampling.NEAREST)

                # 	# Small gradient background. Looks decent, and is only a one-liner.
                # 	# bg = image.copy().resize((2, 2), resample=Image.Resampling.BILINEAR).resize((adj_size,adj_size),resample=Image.Resampling.BILINEAR)

                # 	# Four-Corner Gradient Background.
                # 	# Not exactly a one-liner, but it's (subjectively) really cool.
                # 	tl = image.getpixel((0, 0))
                # 	tr = image.getpixel(((image.size[0]-1), 0))
                # 	bl = image.getpixel((0, (image.size[1]-1)))
                # 	br = image.getpixel(((image.size[0]-1), (image.size[1]-1)))
                # 	bg = Image.new(mode='RGB', size=(2, 2))
                # 	bg.paste(tl, (0, 0, 2, 2))
                # 	bg.paste(tr, (1, 0, 2, 2))
                # 	bg.paste(bl, (0, 1, 2, 2))
                # 	bg.paste(br, (1, 1, 2, 2))
                # 	bg = bg.resize((adj_size, adj_size),
                # 				   resample=Image.Resampling.BICUBIC)

                # 	bg.paste(image, box=(
                # 		(adj_size-image.size[0])//2, (adj_size-image.size[1])//2))

                # 	bg.putalpha(mask)
                # 	final = bg

                # else:
                # 	image.putalpha(mask)
                # 	final = image

                # hl_soft = hl.copy()
                # hl_soft.putalpha(ImageEnhance.Brightness(
                # 	hl.getchannel(3)).enhance(.5))
                # final.paste(ImageChops.soft_light(final, hl_soft),
                # 			mask=hl_soft.getchannel(3))

                # hl_add = hl.copy()
                # hl_add.putalpha(ImageEnhance.Brightness(hl.getchannel(3)).enhance(.25))
                # final.paste(hl_add, mask=hl_add.getchannel(3))
                scalar = 4
                rec: Image.Image = Image.new(
                    "RGB", tuple([d * scalar for d in image.size]), "black"
                )
                draw = ImageDraw.Draw(rec)
                draw.rounded_rectangle(
                    (0, 0) + rec.size,
                    (base_size[0] // 32) * scalar * pixelRatio,
                    fill="red",
                )
                rec = rec.resize(
                    tuple([d // scalar for d in rec.size]),
                    resample=Image.Resampling.BILINEAR,
                )
                # final = image
                final = Image.new("RGBA", image.size, (0, 0, 0, 0))
                # logging.info(rec.size)
                # logging.info(image.size)
                final.paste(image, mask=rec.getchannel(0))

            except (UnidentifiedImageError, FileNotFoundError, cv2.error):
                broken_thumb = True
                self.updated_ratio.emit(1)
                final = ThumbRenderer.thumb_broken_512.resize(
                    (adj_size, adj_size), resample=Image.Resampling.BILINEAR
                )

            # if extension in VIDEO_TYPES + ['gif', 'apng'] or broken_thumb:
            # 	idk = ImageDraw.Draw(final)
            # 	# idk.textlength(file_type)
            # 	ext_offset_x = idk.textlength(
            # 		text=extension.upper(), font=ThumbRenderer.ext_font) / 2
            # 	ext_offset_x = math.floor(ext_offset_x * (1/pixelRatio))
            # 	x_margin = math.floor(
            # 		(adj_size-((base_size[0]//6)+ext_offset_x) * pixelRatio))
            # 	y_margin = math.floor(
            # 		(adj_size-((base_size[0]//8)) * pixelRatio))
            # 	stroke_width = round(2 * pixelRatio)
            # 	fill = 'white' if not broken_thumb else '#E32B41'
            # 	idk.text((x_margin, y_margin), extension.upper(
            # 	), fill=fill, font=ThumbRenderer.ext_font, stroke_width=stroke_width, stroke_fill=(0, 0, 0))

            qim = ImageQt.ImageQt(final)
            if image:
                image.close()
            pixmap = QPixmap.fromImage(qim)
            pixmap.setDevicePixelRatio(pixelRatio)

        if pixmap:
            # logging.info(final.size)
            # self.updated.emit(pixmap, QSize(*final.size))
            self.updated.emit(
                timestamp,
                pixmap,
                QSize(
                    math.ceil(adj_size * 1 / pixelRatio),
                    math.ceil(final.size[1] * 1 / pixelRatio),
                ),
                extension,
            )

        else:
            self.updated.emit(timestamp, QPixmap(), QSize(*base_size), extension)
