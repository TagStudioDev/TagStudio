# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import platform
import traceback
from enum import IntEnum
from typing import Any

import structlog
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication, QPalette

from tagstudio.core.library.alchemy.enums import TagColorEnum
from tagstudio.core.utils.singleton import Singleton

logger = structlog.get_logger(__name__)

# TODO: Completely rework the color palette system, including this file.

# A translucent purple for de-emphasized text and lines, like the copyright and version dates
MUTED_PURPLE = "#809782ff"
MUTED_PURPLE_OPAQUE = "#9782ff"


class Palette(metaclass=Singleton):
    _palette: QPalette | None = None

    @staticmethod
    def set_palette(palette: QPalette) -> None:
        Palette._palette = palette

    @staticmethod
    def accent() -> QColor:
        # NOTE: As of PySide 6.8.0.1, the QPalette.ColorRole.Accent role no longer works on Windows.
        # The QPalette.ColorRole.Highlight does for some reason, but is faded on macOS.

        if not Palette._palette:
            logger.error("[Style] No QPalette set!")
            return QColor.fromString(get_ui_color(ColorType.PRIMARY, UiColor.BLUE))
        role = (
            QPalette.ColorRole.Highlight
            if platform.system() == "Windows"
            else QPalette.ColorRole.Accent
        )

        return QPalette.color(Palette._palette, role)

    @staticmethod
    def icon() -> QColor:
        """The translucent gray of default file icons and resize handles."""
        is_dark = QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
        return QColor(ICON_COLORS[UiColor.THEME_DARK if is_dark else UiColor.THEME_LIGHT])

    @staticmethod
    def contrast() -> QColor:
        """Solid white in dark mode and solid black in light mode."""
        is_dark = QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
        return QColor(Qt.GlobalColor.white if is_dark else Qt.GlobalColor.black)

    @staticmethod
    def accent_alt() -> QColor:
        """An alternate accent color variant that's lighter in dark mode."""
        return QColor(
            Palette.accent().lighter(110)
            if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
            else Palette.accent()
        )


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
    ORANGE = 4
    AMBER = 5
    GREEN = 6
    BLUE = 7
    PURPLE = 8


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
    UiColor.ORANGE: {
        ColorType.PRIMARY: "#FF8020",
        ColorType.BORDER: "#E86919",
        ColorType.LIGHT_ACCENT: "#FFECB3",
        ColorType.DARK_ACCENT: "#752809",
    },
    UiColor.AMBER: {
        ColorType.PRIMARY: "#FFC107",
        ColorType.BORDER: "#FFD54F",
        ColorType.LIGHT_ACCENT: "#FFECB3",
        ColorType.DARK_ACCENT: "#772505",
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

ICON_COLORS = {
    UiColor.THEME_DARK: QColor(255, 255, 255, 56),
    UiColor.THEME_LIGHT: QColor(0, 0, 0, 112),
}


def blend(a: QColor, b: QColor, amount: float) -> QColor:
    """The color `amount` of the way from a to b."""
    return QColor(
        round(a.red() + (b.red() - a.red()) * amount),
        round(a.green() + (b.green() - a.green()) * amount),
        round(a.blue() + (b.blue() - a.blue()) * amount),
        round(a.alpha() + (b.alpha() - a.alpha()) * amount),
    )


def burn(base: int, top: int) -> int:
    """One channel of a color burn blend."""
    return 0 if top == 0 else max(0, 255 - (255 - base) * 255 // top)


def screen(base: int, top: int) -> int:
    """One channel of a screen blend."""
    return 255 - (255 - base) * (255 - top) // 255


def shade(color: QColor, darkness: float, burn_amount: float) -> QColor:
    """The color taken toward black, then tinted by color burning the color over it."""
    darkened = blend(color, QColor(Qt.GlobalColor.black), darkness)
    burned = QColor(
        burn(darkened.red(), color.red()),
        burn(darkened.green(), color.green()),
        burn(darkened.blue(), color.blue()),
        darkened.alpha(),
    )
    return blend(darkened, burned, burn_amount)


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
