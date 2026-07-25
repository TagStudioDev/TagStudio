#!/usr/bin/env python3
# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


# <pep8 compliant>


## This file is a modified script that gets the thumbnail data stored in a blend file


import gzip
import os
import struct
from io import BufferedReader

from PIL import Image, ImageOps


def blend_extract_thumb(path) -> tuple[bytes | None, int, int]:
    rend = b"REND"
    test = b"TEST"

    blendfile: BufferedReader | gzip.GzipFile = open(path, "rb")  # noqa: SIM115

    head = blendfile.read(12)

    if head[0:2] == b"\x1f\x8b":  # gzip magic
        blendfile.close()
        blendfile = gzip.GzipFile("", "rb", 0, open(path, "rb"))  # noqa: SIM115
        head = blendfile.read(12)

    if not head.startswith(b"BLENDER"):
        blendfile.close()
        return None, 0, 0

    is_64_bit = head[7] == b"-"[0]

    # true for PPC, false for X86
    is_big_endian = head[8] == b"V"[0]

    # blender pre 2.5 had no thumbs
    if head[9:11] <= b"24":
        return None, 0, 0

    sizeof_bhead = 24 if is_64_bit else 20
    int_endian = ">i" if is_big_endian else "<i"
    int_endian_pair = int_endian + "i"

    while True:
        bhead = blendfile.read(sizeof_bhead)

        if len(bhead) < sizeof_bhead:
            return None, 0, 0

        code = bhead[:4]
        length = struct.unpack(int_endian, bhead[4:8])[0]  # 4 == sizeof(int)

        if code == rend:
            blendfile.seek(length, os.SEEK_CUR)
        else:
            break

    if code != test:
        return None, 0, 0

    try:
        x, y = struct.unpack(int_endian_pair, blendfile.read(8))  # 8 == sizeof(int) * 2
    except struct.error:
        return None, 0, 0

    length -= 8  # sizeof(int) * 2

    if length != x * y * 4:
        return None, 0, 0

    image_buffer = blendfile.read(length)

    if len(image_buffer) != length:
        return None, 0, 0

    return image_buffer, x, y


def blend_thumb(file_in) -> Image.Image | None:
    buf, width, height = blend_extract_thumb(file_in)
    if buf is None:
        return None
    image = Image.frombuffer(
        "RGBA",
        (width, height),
        buf,
    )
    image = ImageOps.flip(image)
    return image
