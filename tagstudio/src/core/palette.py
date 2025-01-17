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
    },
    TagColorEnum.BLACK: {
        ColorType.PRIMARY: "#111018",
        ColorType.TEXT: ColorType.LIGHT_ACCENT,
        ColorType.BORDER: "#18171e",
        ColorType.LIGHT_ACCENT: "#b7b6be",
        ColorType.DARK_ACCENT: "#03020a",
    },
    TagColorEnum.DARK_GRAY: {
        ColorType.PRIMARY: "#24232a",
        ColorType.TEXT: ColorType.LIGHT_ACCENT,
        ColorType.BORDER: "#2a2930",
        ColorType.LIGHT_ACCENT: "#bdbcc4",
        ColorType.DARK_ACCENT: "#07060e",
    },
    TagColorEnum.GRAY: {
        ColorType.PRIMARY: "#53525a",
        ColorType.TEXT: ColorType.LIGHT_ACCENT,
        ColorType.BORDER: "#5b5a62",
        ColorType.LIGHT_ACCENT: "#cbcad2",
        ColorType.DARK_ACCENT: "#191820",
    },
    TagColorEnum.LIGHT_GRAY: {
        ColorType.PRIMARY: "#aaa9b0",
        ColorType.TEXT: ColorType.DARK_ACCENT,
        ColorType.BORDER: "#b6b4bc",
        ColorType.LIGHT_ACCENT: "#cbcad2",
        ColorType.DARK_ACCENT: "#191820",
    },
    TagColorEnum.WHITE: {
        ColorType.PRIMARY: "#f2f1f8",
        ColorType.TEXT: ColorType.DARK_ACCENT,
        ColorType.BORDER: "#fefeff",
        ColorType.LIGHT_ACCENT: "#ffffff",
        ColorType.DARK_ACCENT: "#302f36",
    },
    TagColorEnum.LIGHT_PINK: {
        ColorType.PRIMARY: "#ff99c4",
        ColorType.TEXT: ColorType.DARK_ACCENT,
        ColorType.BORDER: "#ffaad0",
        ColorType.LIGHT_ACCENT: "#ffcbe7",
        ColorType.DARK_ACCENT: "#6c2e3b",
    },
    TagColorEnum.PINK: {
        ColorType.PRIMARY: "#F96BB1",
        ColorType.TEXT: ColorType.DARK_ACCENT,
        ColorType.BORDER: "#FA7EBC",
        ColorType.LIGHT_ACCENT: "#FDB6DC",
        ColorType.DARK_ACCENT: "#5B2135",
    },
    TagColorEnum.MAGENTA: {
        ColorType.PRIMARY: "#f6466f",
        ColorType.TEXT: ColorType.DARK_ACCENT,
        ColorType.BORDER: "#f7587f",
        ColorType.LIGHT_ACCENT: "#fba4bf",
        ColorType.DARK_ACCENT: "#61152f",
    },
    TagColorEnum.RED: {
        ColorType.PRIMARY: "#e22c3c",
        ColorType.TEXT: ColorType.DARK_ACCENT,
        ColorType.BORDER: "#e54252",
        ColorType.LIGHT_ACCENT: "#f39caa",
        ColorType.DARK_ACCENT: "#440d12",
    },
    TagColorEnum.RED_ORANGE: {
        ColorType.PRIMARY: "#e83726",
        ColorType.TEXT: ColorType.DARK_ACCENT,
        ColorType.BORDER: "#ea4b3b",
        ColorType.LIGHT_ACCENT: "#f5a59d",
        ColorType.DARK_ACCENT: "#61120b",
    },
    TagColorEnum.SALMON: {
        ColorType.PRIMARY: "#f65848",
        ColorType.TEXT: ColorType.DARK_ACCENT,
        ColorType.BORDER: "#f76c5f",
        ColorType.LIGHT_ACCENT: "#fcadaa",
        ColorType.DARK_ACCENT: "#6f1b16",
    },
    TagColorEnum.ORANGE: {
        ColorType.PRIMARY: "#ed6022",
        ColorType.TEXT: ColorType.DARK_ACCENT,
        ColorType.BORDER: "#ef7038",
        ColorType.LIGHT_ACCENT: "#f7b79b",
        ColorType.DARK_ACCENT: "#551e0a",
    },
    TagColorEnum.YELLOW_ORANGE: {
        ColorType.PRIMARY: "#fa9a2c",
        ColorType.TEXT: ColorType.DARK_ACCENT,
        ColorType.BORDER: "#fba94b",
        ColorType.LIGHT_ACCENT: "#fdd7ab",
        ColorType.DARK_ACCENT: "#66330d",
    },
    TagColorEnum.YELLOW: {
        ColorType.PRIMARY: "#ffd63d",
        ColorType.TEXT: ColorType.DARK_ACCENT,
        ColorType.BORDER: "#ffe071",
        ColorType.LIGHT_ACCENT: "#fff3c4",
        ColorType.DARK_ACCENT: "#754312",
    },
    TagColorEnum.MINT: {
        ColorType.PRIMARY: "#4aed90",
        ColorType.TEXT: ColorType.DARK_ACCENT,
        ColorType.BORDER: "#79f2b1",
        ColorType.LIGHT_ACCENT: "#c8fbe9",
        ColorType.DARK_ACCENT: "#164f3e",
    },
    TagColorEnum.LIME: {
        ColorType.PRIMARY: "#92e649",
        ColorType.TEXT: ColorType.DARK_ACCENT,
        ColorType.BORDER: "#b2ed72",
        ColorType.LIGHT_ACCENT: "#e9f9b7",
        ColorType.DARK_ACCENT: "#405516",
    },
    TagColorEnum.LIGHT_GREEN: {
        ColorType.PRIMARY: "#85ec76",
        ColorType.TEXT: ColorType.DARK_ACCENT,
        ColorType.BORDER: "#a3f198",
        ColorType.LIGHT_ACCENT: "#e7fbe4",
        ColorType.DARK_ACCENT: "#2b5524",
    },
    TagColorEnum.GREEN: {
        ColorType.PRIMARY: "#28bb48",
        ColorType.TEXT: ColorType.DARK_ACCENT,
        ColorType.BORDER: "#43c568",
        ColorType.LIGHT_ACCENT: "#93e2c8",
        ColorType.DARK_ACCENT: "#0d3828",
    },
    TagColorEnum.TEAL: {
        ColorType.PRIMARY: "#1ad9b2",
        ColorType.TEXT: ColorType.DARK_ACCENT,
        ColorType.BORDER: "#4de3c7",
        ColorType.LIGHT_ACCENT: "#a0f3e8",
        ColorType.DARK_ACCENT: "#08424b",
    },
    TagColorEnum.CYAN: {
        ColorType.PRIMARY: "#49e4d5",
        ColorType.TEXT: ColorType.DARK_ACCENT,
        ColorType.BORDER: "#76ebdf",
        ColorType.LIGHT_ACCENT: "#bff5f0",
        ColorType.DARK_ACCENT: "#0f4246",
    },
    TagColorEnum.LIGHT_BLUE: {
        ColorType.PRIMARY: "#55bbf6",
        ColorType.TEXT: ColorType.DARK_ACCENT,
        ColorType.BORDER: "#70c6f7",
        ColorType.LIGHT_ACCENT: "#bbe4fb",
        ColorType.DARK_ACCENT: "#122541",
    },
    TagColorEnum.BLUE: {
        ColorType.PRIMARY: "#3b87f0",
        ColorType.TEXT: ColorType.LIGHT_ACCENT,
        ColorType.BORDER: "#4e95f2",
        ColorType.LIGHT_ACCENT: "#aedbfa",
        ColorType.DARK_ACCENT: "#122948",
    },
    TagColorEnum.BLUE_VIOLET: {
        ColorType.PRIMARY: "#5948f2",
        ColorType.TEXT: ColorType.LIGHT_ACCENT,
        ColorType.BORDER: "#6258f3",
        ColorType.LIGHT_ACCENT: "#9cb8fb",
        ColorType.DARK_ACCENT: "#1b1649",
    },
    TagColorEnum.VIOLET: {
        ColorType.PRIMARY: "#874ff5",
        ColorType.TEXT: ColorType.LIGHT_ACCENT,
        ColorType.BORDER: "#9360f6",
        ColorType.LIGHT_ACCENT: "#c9b0fa",
        ColorType.DARK_ACCENT: "#3a1860",
    },
    TagColorEnum.PURPLE: {
        ColorType.PRIMARY: "#bb4ff0",
        ColorType.TEXT: ColorType.DARK_ACCENT,
        ColorType.BORDER: "#c364f2",
        ColorType.LIGHT_ACCENT: "#dda7f7",
        ColorType.DARK_ACCENT: "#531862",
    },
    TagColorEnum.PEACH: {
        ColorType.PRIMARY: "#f1c69c",
        ColorType.TEXT: ColorType.DARK_ACCENT,
        ColorType.BORDER: "#f4d4b4",
        ColorType.LIGHT_ACCENT: "#fbeee1",
        ColorType.DARK_ACCENT: "#613f2f",
    },
    TagColorEnum.BROWN: {
        ColorType.PRIMARY: "#823216",
        ColorType.TEXT: ColorType.LIGHT_ACCENT,
        ColorType.BORDER: "#8a3e22",
        ColorType.LIGHT_ACCENT: "#cd9d83",
        ColorType.DARK_ACCENT: "#3a1804",
    },
    TagColorEnum.LAVENDER: {
        ColorType.PRIMARY: "#ad8eef",
        ColorType.TEXT: ColorType.DARK_ACCENT,
        ColorType.BORDER: "#b99ef2",
        ColorType.LIGHT_ACCENT: "#d5c7fa",
        ColorType.DARK_ACCENT: "#492b65",
    },
    TagColorEnum.BLONDE: {
        ColorType.PRIMARY: "#efc664",
        ColorType.TEXT: ColorType.DARK_ACCENT,
        ColorType.BORDER: "#f3d387",
        ColorType.LIGHT_ACCENT: "#faebc6",
        ColorType.DARK_ACCENT: "#6d461e",
    },
    TagColorEnum.AUBURN: {
        ColorType.PRIMARY: "#a13220",
        ColorType.TEXT: ColorType.LIGHT_ACCENT,
        ColorType.BORDER: "#aa402f",
        ColorType.LIGHT_ACCENT: "#d98a7f",
        ColorType.DARK_ACCENT: "#3d100a",
    },
    TagColorEnum.LIGHT_BROWN: {
        ColorType.PRIMARY: "#be5b2d",
        ColorType.TEXT: ColorType.DARK_ACCENT,
        ColorType.BORDER: "#c4693d",
        ColorType.LIGHT_ACCENT: "#e5b38c",
        ColorType.DARK_ACCENT: "#4c290e",
    },
    TagColorEnum.DARK_BROWN: {
        ColorType.PRIMARY: "#4c2315",
        ColorType.TEXT: ColorType.LIGHT_ACCENT,
        ColorType.BORDER: "#542a1c",
        ColorType.LIGHT_ACCENT: "#b78171",
        ColorType.DARK_ACCENT: "#211006",
    },
    TagColorEnum.COOL_GRAY: {
        ColorType.PRIMARY: "#515768",
        ColorType.TEXT: ColorType.LIGHT_ACCENT,
        ColorType.BORDER: "#5b6174",
        ColorType.LIGHT_ACCENT: "#9ea1c3",
        ColorType.DARK_ACCENT: "#181a37",
    },
    TagColorEnum.WARM_GRAY: {
        ColorType.PRIMARY: "#625550",
        ColorType.TEXT: ColorType.LIGHT_ACCENT,
        ColorType.BORDER: "#6c5e57",
        ColorType.LIGHT_ACCENT: "#c0a392",
        ColorType.DARK_ACCENT: "#371d18",
    },
    TagColorEnum.OLIVE: {
        ColorType.PRIMARY: "#4c652e",
        ColorType.TEXT: ColorType.LIGHT_ACCENT,
        ColorType.BORDER: "#586f36",
        ColorType.LIGHT_ACCENT: "#b4c17a",
        ColorType.DARK_ACCENT: "#23300e",
    },
    TagColorEnum.BERRY: {
        ColorType.PRIMARY: "#9f2aa7",
        ColorType.TEXT: ColorType.LIGHT_ACCENT,
        ColorType.BORDER: "#aa43b4",
        ColorType.LIGHT_ACCENT: "#cc8fdc",
        ColorType.DARK_ACCENT: "#41114a",
    },
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
