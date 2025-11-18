#!/usr/bin/env python3

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>


## This file is a modified script that gets the thumbnail data stored in a blend file


import gzip
import os
import struct
from io import BufferedReader

import structlog
from PIL import Image, ImageOps, UnidentifiedImageError
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication

from tagstudio.qt.previews.renderers.base_renderer import BaseRenderer, RendererContext

logger = structlog.get_logger(__name__)


class BlenderRenderer(BaseRenderer):
    def __init__(self):
        super().__init__()

    @staticmethod
    def render(context: RendererContext) -> Image.Image | None:
        """Get an emended thumbnail from a Blender file, if a thumbnail is present.

        Args:
            context (RendererContext): The renderer context.
        """
        bg_color: str = (
            "#1e1e1e"
            if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
            else "#FFFFFF"
        )

        try:
            buffer, width, height = BlenderRenderer.__extract_embedded_thumbnail(str(context.path))

            if buffer is None:
                return None

            embedded_thumbnail = Image.frombuffer(
                "RGBA",
                (width, height),
                buffer,
            )
            embedded_thumbnail = ImageOps.flip(embedded_thumbnail)

            rendered_image = Image.new("RGB", embedded_thumbnail.size, color=bg_color)
            rendered_image.paste(embedded_thumbnail, mask=embedded_thumbnail.getchannel(3))
            return rendered_image

        except (
            AttributeError,
            UnidentifiedImageError,
            TypeError,
        ) as e:
            if str(e) == "expected string or buffer":
                logger.info(
                    f"[BlenderRenderer] {context.path.name} "
                    f"doesn't have an embedded thumbnail. ({e})"
                )

            else:
                logger.error("Couldn't render thumbnail", path=context.path, error=e)

        return None

    @staticmethod
    def __extract_embedded_thumbnail(path) -> tuple[bytes | None, int, int]:
        rend = b"REND"
        test = b"TEST"

        blender_file: BufferedReader | gzip.GzipFile = open(path, "rb")  # noqa: SIM115

        header = blender_file.read(12)

        if header[0:2] == b"\x1f\x8b":  # gzip magic
            blender_file.close()
            blender_file = gzip.GzipFile("", "rb", 0, open(path, "rb"))  # noqa: SIM115
            header = blender_file.read(12)

        if not header.startswith(b"BLENDER"):
            blender_file.close()
            return None, 0, 0

        is_64_bit = header[7] == b"-"[0]

        # True for PPC, false for X86
        is_big_endian = header[8] == b"V"[0]

        # Blender pre-v2.5 had no thumbnails
        if header[9:11] <= b"24":
            return None, 0, 0

        block_header_size = 24 if is_64_bit else 20
        int_endian = ">i" if is_big_endian else "<i"
        int_endian_pair = int_endian + "i"

        # Continually read through file blocks until encountering a render thumbnail
        while True:
            block_header = blender_file.read(block_header_size)

            if len(block_header) < block_header_size:
                return None, 0, 0

            block_code = block_header[:4]  # (The 'code' is the block's identifier)
            length = struct.unpack(int_endian, block_header[4:8])[0]  # 4 == sizeof(int)

            if block_code == rend:
                blender_file.seek(length, os.SEEK_CUR)
            else:
                break

        if block_code != test:
            return None, 0, 0

        try:
            width, height = struct.unpack(
                int_endian_pair, blender_file.read(8)
            )  # 8 == sizeof(int) * 2
        except struct.error:
            return None, 0, 0

        length -= 8  # sizeof(int) * 2

        if length != width * height * 4:
            return None, 0, 0

        image_buffer = blender_file.read(length)

        if len(image_buffer) != length:
            return None, 0, 0

        return image_buffer, width, height
