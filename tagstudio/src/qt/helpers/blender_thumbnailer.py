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


import struct


def open_wrapper_get():
    """wrap OS specific read functionality here, fallback to 'open()'"""

    def open_local_url(url, mode="r"):
        # Redundant af, but this is where the checking of file path can be done

        path = url

        return open(str(path), mode)

    return open_local_url


def blend_extract_thumb(path):
    import os

    open_wrapper = open_wrapper_get()

    REND = b"REND"
    TEST = b"TEST"

    blendfile = open_wrapper(path, "rb")

    head = blendfile.read(12)

    if head[0:2] == b"\x1f\x8b":  # gzip magic
        import gzip

        blendfile.close()
        blendfile = gzip.GzipFile("", "rb", 0, open_wrapper(path, "rb"))
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

        if code == REND:
            blendfile.seek(length, os.SEEK_CUR)
        else:
            break

    if code != TEST:
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


# Trying to flip image buffer to have the image right way round on the output, but can't figure it out
# Currently, just flipping it with ImageOps in the thumbnail_renderer.py

##def flip_image(buf, width, height):
##    import zlib
##
##    # reverse the vertical line order and add null bytes at the start
##    width_byte_4 = width * 4
##    raw_data = b"".join(b'\x00' + buf[span:span + width_byte_4] for span in range((height - 1) * width * 4, -1, - width_byte_4))
##
##    def png_pack(png_tag, data):
##        chunk_head = png_tag + data
##        return struct.pack("!I", len(data)) + chunk_head + struct.pack("!I", 0xFFFFFFFF & zlib.crc32(chunk_head))
##
##    return [b"".join([
##        b'\x89PNG\r\n\x1a\n',
##        png_pack(b'IHDR', struct.pack("!2I5B", width, height, 8, 6, 0, 0, 0)),
##        png_pack(b'IDAT', zlib.compress(raw_data, 9)),
##        png_pack(b'IEND', b'')]), width, height]


def blendthumb(file_in):
    buf, width, height = blend_extract_thumb(file_in)
    return [buf, width, height]
