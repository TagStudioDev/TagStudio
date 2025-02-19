# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio
import traceback
from enum import IntEnum
from typing import Any

import structlog
from src.core.library.alchemy.enums import TagColorEnum

logger = structlog.get_logger(__name__)


class ColorType(IntEnum):
    PRIMARY = 0
    TEXT = 1
    BORDER = 2
    LIGHT_ACCENT = 3
    DARK_ACCENT = 4


class UiColor(IntEnum):
    DEFAULT = 0
    THEME_DARK = 1
    THEME_LIGHT = 2
    RED = 3
    GREEN = 4
    BLUE = 5
    PURPLE = 6


TAG_COLORS: dict[TagColorEnum, dict[ColorType, Any]] = {
    TagColorEnum.DEFAULT: {
        ColorType.PRIMARY: "#1e1e1e",
        ColorType.TEXT: ColorType.LIGHT_ACCENT,
        ColorType.BORDER: "#333333",
        ColorType.LIGHT_ACCENT: "#FFFFFF",
        ColorType.DARK_ACCENT: "#222222",
    }
}

UI_COLORS: dict[UiColor, dict[ColorType, Any]] = {
    UiColor.DEFAULT: {
        ColorType.PRIMARY: "#333333",
        ColorType.BORDER: "#555555",
        ColorType.LIGHT_ACCENT: "#FFFFFF",
        ColorType.DARK_ACCENT: "#1e1e1e",
    },
    UiColor.RED: {
        ColorType.PRIMARY: "#e22c3c",
        ColorType.BORDER: "#e54252",
        ColorType.LIGHT_ACCENT: "#f39caa",
        ColorType.DARK_ACCENT: "#440d12",
    },
    UiColor.GREEN: {
        ColorType.PRIMARY: "#28bb48",
        ColorType.BORDER: "#43c568",
        ColorType.LIGHT_ACCENT: "#DDFFCC",
        ColorType.DARK_ACCENT: "#0d3828",
    },
    UiColor.BLUE: {
        ColorType.PRIMARY: "#3b87f0",
        ColorType.BORDER: "#4e95f2",
        ColorType.LIGHT_ACCENT: "#aedbfa",
        ColorType.DARK_ACCENT: "#122948",
    },
    UiColor.PURPLE: {
        ColorType.PRIMARY: "#C76FF3",
        ColorType.BORDER: "#c364f2",
        ColorType.LIGHT_ACCENT: "#EFD4FB",
        ColorType.DARK_ACCENT: "#3E1555",
    },
    UiColor.THEME_DARK: {
        ColorType.PRIMARY: "#333333",
        ColorType.BORDER: "#555555",
        ColorType.LIGHT_ACCENT: "#FFFFFF",
        ColorType.DARK_ACCENT: "#1e1e1e",
    },
    UiColor.THEME_LIGHT: {
        ColorType.PRIMARY: "#FFFFFF",
        ColorType.BORDER: "#333333",
        ColorType.LIGHT_ACCENT: "#999999",
        ColorType.DARK_ACCENT: "#888888",
    },
}


def get_tag_color(color_type: ColorType, color_id: TagColorEnum) -> str:
    """Return a hex value given a tag color name and ColorType.

    Args:
        color_type (ColorType): The ColorType category to retrieve from.
        color_id (ColorType): The color name enum to retrieve from.

    Return:
        A hex value string representing a color with a leading "#".
    """
    try:
        if color_type == ColorType.TEXT:
            text_account: ColorType = TAG_COLORS[color_id][color_type]
            return get_tag_color(text_account, color_id)

        return TAG_COLORS[color_id][color_type]
    except KeyError:
        traceback.print_stack()
        logger.error("[PALETTE] Tag color not found.", color_id=color_id)
        return "#FF00FF"


def get_ui_color(color_type: ColorType, color_id: UiColor) -> str:
    """Return a hex value given a UI color name and ColorType.

    Args:
        color_type (ColorType): The ColorType category to retrieve from.
        color_id (UiColor): The color name enum to retrieve from.

    Return:
        A hex value string representing a color with a leading "#".
    """
    try:
        return UI_COLORS[color_id][color_type]
    except KeyError:
        traceback.print_stack()
        logger.error("[PALETTE] UI color not found", color_id=color_id)
        return "#FF00FF"
