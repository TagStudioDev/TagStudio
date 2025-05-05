# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from PIL import Image, ImageDraw, ImageFont


def wrap_line(
    text: str,
    font: ImageFont.ImageFont,
    width: int = 256,
    draw: ImageDraw.ImageDraw | None = None,
) -> int:
    """Take in a single text line and return the index it should be broken up at.

    Only splits once.
    """
    if draw is None:
        bg = Image.new("RGB", (width, width), color="#1e1e1e")
        draw = ImageDraw.Draw(bg)
    if draw.textlength(text, font=font) > width:
        for i in range(
            int(len(text) / int(draw.textlength(text, font=font)) * width) - 2,
            0,
            -1,
        ):
            if draw.textlength(text[:i], font=font) < width:
                return i
    return -1


def wrap_full_text(
    text: str,
    font: ImageFont.ImageFont,
    width: int = 256,
    draw: ImageDraw.ImageDraw | None = None,
) -> str:
    """Break up a string to fit the canvas given a kerning value, font size, etc."""
    lines = []
    i = 0
    last_i = 0
    while wrap_line(text[i:], font=font, width=width, draw=draw) > 0:
        i = wrap_line(text[i:], font=font, width=width, draw=draw) + last_i
        lines.append(text[last_i:i])
        last_i = i
    lines.append(text[last_i:])
    text_wrapped = "\n".join(lines)
    return text_wrapped
