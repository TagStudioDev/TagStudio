# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from enum import Enum

from PySide6.QtGui import QColor

class ColorType(int, Enum):
    PRIMARY = 0
    TEXT = 1
    BORDER = 2
    LIGHT_ACCENT = 3
    DARK_ACCENT = 4

def get_tag_color(color_type: ColorType, color: str):
    """ Simple wrapper around get_accent_color to support treating colors as strings """
    return qcolor_to_hex(get_accent_color(color_type, QColor.fromString(color)))

def get_accent_color(color_type: ColorType, color: QColor):
    """ Adjust the input color by effects to generate accenting colors """
    match color_type:
        case ColorType.TEXT:
            if (color.red() * 0.299 + color.green() * 0.587 + color.blue() * 0.114) > 186:
                return QColor.fromString("#000000")
            else:
                return QColor.fromString("#FFFFFF")
        case ColorType.BORDER:
            return QColor.fromHsv(color.hue(), int(color.saturation() * 0.75), int(color.value() * 0.75))
        case ColorType.LIGHT_ACCENT:
            return color.lighter(150)
        case ColorType.DARK_ACCENT:
            return color.darker(150)
        case _:
            return color

def qcolor_to_hex(color: QColor):
    return color.name(QColor.NameFormat.HexRgb)

