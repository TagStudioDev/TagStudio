# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from PIL import Image, ImageDraw, ImageFont


def wrap_line(  # type: ignore
    text: str,
    font: ImageFont.ImageFont,
    width: int = 256,
    draw: ImageDraw.ImageDraw = None,
) -> int:
    """
    Takes in a single line and returns the index it should be broken up at but
    it only splits one Time
    """
    if draw is None:
        bg = Image.new("RGB", (width, width), color="#1e1e1e")
        draw = ImageDraw.Draw(bg)
    if draw.textlength(text, font=font) > 256:
        # print(draw.textlength(text, font=font))
        for i in range(
            int(len(text) / int(draw.textlength(text, font=font)) * 256) - 2,
            0,
            -1,
        ):
            if draw.textlength(text[:i], font=font) < 256:
                # print(len(text))
                # print(i)
                return i
    else:
        return -1


def wrap_full_text(
    text: str,
    font: ImageFont.ImageFont,
    width: int = 256,
    draw: ImageDraw.ImageDraw = None,
) -> str:
    """
    Takes in a string and breaks it up to fit in the canvas given accounts for kerning and font size etc.
    """
    lines = []
    i = 0
    last_i = 0
    while wrap_line(text[i:], font=font, width=width, draw=draw) > 0:
        i = wrap_line(text[i:], font=font, draw=draw) + last_i
        lines.append(text[last_i:i])
        last_i = i
    lines.append(text[last_i:])
    text_wrapped = "\n".join(lines)
    return text_wrapped
