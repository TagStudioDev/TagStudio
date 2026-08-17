# SPDX-FileCopyrightText: (c) 2017 Blender Foundation
# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

"""Extract an embedded thumbnail from a Blender file."""

import gzip
import os
import struct
from pathlib import Path
from typing import BinaryIO

from PIL import Image, ImageOps


def blend_extract_thumb(path: Path | str) -> tuple[bytes | None, int, int]:
    REND: bytes = b"REND"
    TEST: bytes = b"TEST"
    ENDB: bytes = b"ENDB"

    blendfile: BinaryIO | gzip.GzipFile | None = None
    raw_file: BinaryIO | None = None

    try:
        # --------------------------------------------------------------
        # Open file.
        # --------------------------------------------------------------
        raw_file = open(path, "rb")

        # Legacy header = 12 bytes
        # Blender 5+   = 17 bytes
        head: bytes = raw_file.read(17)

        # --------------------------------------------------------------
        # GZIP-compressed blend file.
        # --------------------------------------------------------------
        if head[:2] == b"\x1f\x8b":
            raw_file.close()
            raw_file = None

            blendfile = gzip.open(path, "rb")
            head = blendfile.read(17)
        else:
            blendfile = raw_file

        if not head.startswith(b"BLENDER"):
            return None, 0, 0

        if len(head) < 12:
            return None, 0, 0

        # --------------------------------------------------------------
        # Blender 5.0+ header
        #
        #   BLENDER17-01v0501
        #   01234567890123456
        #
        #   0-6   = BLENDER
        #   7-8   = header size
        #   9     = '-'
        #   10-11 = header format
        #   12    = 'v'
        #   13-16 = Blender version
        # --------------------------------------------------------------
        is_blender_5: bool = (
            len(head) >= 17 and head[7:9].isdigit() and head[9:13] == b"-01v"  # format
        )

        if is_blender_5:
            try:
                header_size: int = int(head[7:9])
                version: int = int(head[13:17])
            except ValueError:
                return None, 0, 0

            if header_size < 17:
                return None, 0, 0

            # We have already consumed 17 bytes.
            if header_size > 17:
                blendfile.seek(header_size - 17, os.SEEK_CUR)

            # ----------------------------------------------------------
            # Blender 5+ BHead
            #
            # 0-3    code
            # 4-7    SDNA index (uint32)
            # 8-15   old pointer (uint64)
            # 16-23  block size (uint64)
            # 24-31  count (uint64)
            #
            # Total = 32 bytes.
            # ----------------------------------------------------------
            sizeof_bhead: int = 32
            large_bhead: bool = True

            int_endian: str = "<"
            int_endian_pair: str = "<ii"

        # --------------------------------------------------------------
        # Legacy Blender header
        #
        #   BLENDER-v400
        #
        #   7     pointer size
        #         '-' = 64-bit
        #         '_' = 32-bit
        #
        #   8     endian
        #         'v' = little endian
        #         'V' = big endian
        #
        #   9-11  Blender version
        # --------------------------------------------------------------
        else:
            is_64_bit: bool = head[7] == ord("-")
            is_big_endian: bool = head[8] == ord("V")

            try:
                version: int = int(head[9:12])
            except ValueError:
                return None, 0, 0

            # Blender pre-2.5 had no thumbnails.
            if version < 250:
                return None, 0, 0

            sizeof_bhead: int = 24 if is_64_bit else 20
            large_bhead = False

            int_endian: str = ">" if is_big_endian else "<"
            int_endian_pair = int_endian + "ii"

            # We read 17 bytes above, but the old header is only 12.
            blendfile.seek(12, os.SEEK_SET)

        # --------------------------------------------------------------
        # Walk the BHeads until we find TEST.
        # --------------------------------------------------------------
        while True:
            bhead: bytes = blendfile.read(sizeof_bhead)

            # ENDB is a special partial BHead.
            if len(bhead) >= 4 and bhead[:4] == ENDB:
                return None, 0, 0

            if len(bhead) < sizeof_bhead:
                return None, 0, 0

            code: bytes = bhead[:4]

            # ----------------------------------------------------------
            # Blender 5+
            #
            # The block size is at offset 16 and is uint64.
            # ----------------------------------------------------------
            if large_bhead:
                length: int = struct.unpack_from(
                    "<Q",
                    bhead,
                    16,
                )[0]

            # ----------------------------------------------------------
            # Legacy Blender
            #
            # code   = 0-3
            # length = 4-7
            # old    = 8-11/15
            # SDNA   = ...
            # count  = ...
            # ----------------------------------------------------------
            else:
                length = struct.unpack_from(
                    int_endian + "i",
                    bhead,
                    4,
                )[0]

            # ----------------------------------------------------------
            # REND contains render information before TEST.
            # Skip its payload.
            # ----------------------------------------------------------
            if code == REND:
                if length < 0:
                    return None, 0, 0

                blendfile.seek(length, os.SEEK_CUR)
                continue

            # First non-REND block.
            break

        # --------------------------------------------------------------
        # We need the TEST block.
        # --------------------------------------------------------------
        if code != TEST:
            return None, 0, 0

        # --------------------------------------------------------------
        # TEST payload:
        #
        #   int32 width
        #   int32 height
        #   RGBA pixel data
        # --------------------------------------------------------------
        dimensions: bytes = blendfile.read(8)

        if len(dimensions) != 8:
            return None, 0, 0

        try:
            x: int
            y: int
            x, y = struct.unpack(
                int_endian_pair,
                dimensions,
            )
        except struct.error:
            return None, 0, 0

        # The TEST block length includes the two 32-bit dimensions.
        image_length: int = length - 8

        if x <= 0 or y <= 0:
            return None, 0, 0

        expected_length: int = x * y * 4

        if image_length != expected_length:
            return None, 0, 0

        # --------------------------------------------------------------
        # Read RGBA thumbnail.
        # --------------------------------------------------------------
        image_buffer: bytes = blendfile.read(image_length)

        if len(image_buffer) != image_length:
            return None, 0, 0

        return image_buffer, x, y

    finally:
        if blendfile is not None:
            blendfile.close()

        if raw_file is not None and raw_file is not blendfile:
            raw_file.close()


def blend_thumb(file_in: Path | str) -> Image.Image | None:
    buf, width, height = blend_extract_thumb(file_in)
    if buf is None:
        return None
    image = Image.frombuffer(
        "RGBA",
        (width, height),
        buf,
    )
    image = ImageOps.flip(image)
    # Upscale Image so it looks better at higher resolutions.
    width, height = image.size
    ratio = height / width
    image = image.resize((512, round(512 * ratio)), Image.Resampling.BICUBIC)
    return image
