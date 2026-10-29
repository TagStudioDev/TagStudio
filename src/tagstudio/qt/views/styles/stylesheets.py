# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import platform
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication

from tagstudio.core.enums import ThemePalette
from tagstudio.core.library.alchemy.enums import TagColorEnum
from tagstudio.core.library.alchemy.models import TagColorGroup
from tagstudio.core.utils.singleton import Singleton
from tagstudio.qt.views.styles.palette import (
    ColorType,
    Palette,
    UiColor,
    blend,
    burn,
    get_tag_color,
    get_ui_color,
    screen,
)

# TODO: There's plenty of good opportunities here to consolidate similar styles.
# Work should be done to more closely use Qt's theming systems rather than override them.


RADIUS = 6  # Standard corner radius
LARGE_RADIUS = RADIUS * 2  # Corners of large areas, like the browsing area and pagination bar
INNER_RADIUS = RADIUS // 2  # Inner/small corder radius

OUTLINE_WIDTH = 2  # Hover/selection outlines
RESIZE_HANDLE_LENGTH = 24  # Length of each side of splitter and corner handles
RESIZE_HANDLE_WIDTH = 3
MED_HEIGHT = 30  # Height for medium-sized widgets (all line edits, some buttons)
CHECKBOX_SIZE = 24  # Checkboxes and radio buttons
FLAT_ICON_SIZE = 24  # Icons on flat icon-only buttons, like the mode rail's
CAPSULE_HEIGHT = 24
SWATCH_SIZE = 24

PAD = 6  # Standard padding value
HALF_PAD = PAD // 2
WIN_PAD = 12  # Padding used for window edge margins


class TagShape(metaclass=Singleton):
    """How tags and their badges are shaped."""

    is_pill: bool = True
    is_circle_badge: bool = True
    PILL_INSET_REDUCTION = 2  # Pills tell tiles to have smaller margins for visual balance


def container_style() -> str:
    """Style used for Tile widgets."""
    hover = "#0FFFFFFF" if is_dark_theme() else "#22000000"
    return f"""
    QWidget#tile{{
        border-radius: 4px;
    }}
    QWidget#tile::hover{{
        background-color: {hover};
    }}
    QWidget#tile::pressed{{
        background-color: {ThemePalette.COLOR_PRESSED.value};
    }}
    """


def form_content_style() -> str:
    return f"""
    QLabel{{
        background-color: {
        ThemePalette.COLOR_BG.value
        if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
        else ThemePalette.COLOR_BG_LIGHT.value
    };
        border-radius: {INNER_RADIUS}px;
        font-weight: 500;
        padding: 1px;
    }}
    """


def list_button_style(
    color: QColor | None = None,
    border_style: str = "solid",
    italic: bool = False,
) -> str:
    """Style used for special QPushButtons found in lists."""
    if color is None:
        color = QColor(get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT))

    highlight_color = get_tag_highlight_color(color)
    text_color = get_tag_text_color(color, highlight_color)
    border_color = get_tag_border_color(color)

    return f"""
    QPushButton{{
        background: rgba{color.toTuple()};
        color: rgba{text_color.toTuple()};
        font-weight: 600;
        {"font: italic;" if italic else ""}
        border-color: rgba{border_color.toTuple()};
        border-radius: {RADIUS}px;
        border-style: {border_style};
        border-width: 2px;
        padding-right: 4px;
        padding-bottom: 1px;
        padding-left: 4px;
        font-size: 13px
    }}
    QPushButton::hover{{
        border-color: rgba{highlight_color.toTuple()};
    }}
    QPushButton::pressed{{
        background: rgba{highlight_color.toTuple()};
        color: rgba{color.toTuple()};
        border-color: rgba{color.toTuple()};
    }}
    QPushButton::focus{{
        padding-right: 0px;
        padding-left: 0px;
        outline-style: solid;
        outline-width: 1px;
        outline-radius: 4px;
        outline-color: rgba{text_color.toTuple()};
    }}
    """


def capsule_text_style(
    text_color: QColor,
    pressed_text_color: QColor,
    is_pill: bool,
    left_padding: int | None = None,
    right_padding: int | None = None,
) -> str:
    """Style used for Capsule text."""
    side_padding = 4 + (3 if is_pill else 0)
    return f"""
    QPushButton{{
        background: transparent;
        color: rgba{text_color.toTuple()};
        font-weight: 600;
        border: 2px solid transparent;
        border-radius: {RADIUS}px;
        font-size: 13px;
        padding-right: {side_padding if right_padding is None else right_padding}px;
        padding-left: {side_padding if left_padding is None else left_padding}px;
        padding-bottom: {2 if platform.system() == "Windows" else 1}px;
    }}
    QPushButton::pressed{{
        color: rgba{pressed_text_color.toTuple()};
    }}
    QPushButton::focus{{
        outline: none;
    }}
    """


def capsule_remove_button_style(
    primary_color: QColor,
    text_color: QColor,
    border_color: QColor,
    highlight_color: QColor,
    radius: int | None = None,
) -> str:
    """Style used for "Remove" buttons on Capsules [-]."""
    rest_radius = 5 if radius is None else radius
    hover_radius = RADIUS if radius is None else radius
    return f"""
    QPushButton{{
        color: rgba{primary_color.toTuple()};
        background: rgba{text_color.toTuple()};
        font-weight: 800;
        border-radius: {rest_radius}px;
        border-width: 4;
        border-color: rgba(0,0,0,0);
        padding-bottom: 4px;
        padding-left: 0px;
        padding-right: 0px;
        font-size: 14px
    }}
    QPushButton::hover{{
        background: rgba{primary_color.toTuple()};
        color: rgba{text_color.toTuple()};
        border-color: rgba{highlight_color.toTuple()};
        border-width: 2;
        border-radius: {hover_radius}px;
    }}
    QPushButton::pressed{{
        background: rgba{border_color.toTuple()};
        color: rgba{highlight_color.toTuple()};
    }}
    QPushButton::focus{{
        background: rgba{border_color.toTuple()};
        outline: none;
    }}
    """


def title_line_edit_style() -> str:
    """Used to mimic an H3-like header style inside a QLineEdit."""
    return """
    font-weight: bold;
    font-size: 16px;
    """


def inset_container_style(object_name: str = "") -> str:
    """Used for darkened inset areas, like TileList."""
    return f"""
    QWidget{"#" + object_name if object_name else ""}{{
        background: #00000000;
        }}
    """


def preview_warning_style() -> str:
    return f"""
    QWidget#ffmpeg_widget {{
        background: {get_ui_color(ColorType.DARK_ACCENT, UiColor.RED)};
        border-radius: {RADIUS}px;
        }}
    """


def info_popover_text_style() -> str:
    """Style used for headers inside info popovers, given as a CSS `<style>` tag.

    Used in cases where QSS doesn't work, like for rich text inside QLabels.
    """
    return """
    <style>
        h1, h2, h3, h4, h5, h6 {
            margin-top: 0px;
            margin-bottom: 0px;
        }
    </style>
    """


def is_dark_theme() -> bool:
    return QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark


def get_contrast_text_color(background_color: QColor) -> QColor:
    """Return plain black or white, whichever reads better against `background_color`."""
    return QColor(0, 0, 0) if background_color.lightness() > 140 else QColor(255, 255, 255)


def _banner_button_hover_style(object_name: str) -> str:
    """Shared hover/pressed/focus feedback for the banner's accent-tinted buttons."""
    hover = Palette.accent().darker(140)
    pressed = Palette.accent().lighter(120)
    return f"""
    QPushButton#{object_name}::hover {{
        background-color: rgba{hover.toTuple()};
    }}
    QPushButton#{object_name}::pressed {{
        background-color: rgba{pressed.toTuple()};
    }}
    QPushButton#{object_name}::focus {{
        outline: none;
    }}
    """


def banner_close_button_style() -> str:
    """Style for the banner's close ("X") button in accent-colored notice modes."""
    accent = Palette.accent().darker(180)
    text_color = get_contrast_text_color(accent)

    return f"""
    QPushButton#bannerCloseButton {{
        font-size: 24pt;
        padding-bottom: 4px;
        background: transparent;
        color: rgba{text_color.toTuple()};
        border: none;
        border-radius: {INNER_RADIUS}px;
    }}
    {_banner_button_hover_style("bannerCloseButton")}
    """


def banner_notice_bg_color() -> QColor:
    """Fill color for the banner card in "notice" and "fleeting_notice" modes."""
    color = Palette.accent_alt()
    color.setAlpha(235)
    return color


def banner_notice_style() -> str:
    """Label/button rules for the banner's accent-colored "notice" and "fleeting_notice" modes."""
    accent = Palette.accent()
    text_color = get_contrast_text_color(accent)

    return f"""
    #banner QLabel {{ color: rgba{text_color.toTuple()}; background: transparent; }}
    {banner_close_button_style()}
    """


def banner_close_button_progress_style() -> str:
    """Close button style for the progress banner mode."""
    is_dark = is_dark_theme()
    text_color = QColor(255, 255, 255) if is_dark else QColor(0, 0, 0)
    hover = "rgba(255, 255, 255, 40)" if is_dark else "rgba(0, 0, 0, 40)"
    pressed = "rgba(255, 255, 255, 70)" if is_dark else "rgba(0, 0, 0, 70)"

    return f"""
    QPushButton#bannerCloseButton {{
        font-size: 24pt;
        padding-bottom: 4px;
        background: transparent;
        color: rgba{text_color.toTuple()};
        border: none;
        border-radius: {INNER_RADIUS}px;
    }}
    QPushButton#bannerCloseButton::hover {{
        background-color: {hover};
    }}
    QPushButton#bannerCloseButton::pressed {{
        background-color: {pressed};
    }}
    QPushButton#bannerCloseButton::focus {{
        outline: none;
    }}
    """


def banner_progress_bg_color() -> QColor:
    """Fill color for the banner card in "progress" mode."""
    is_dark = is_dark_theme()
    return QColor(
        ThemePalette.COLOR_BG_DARK.value if is_dark else ThemePalette.COLOR_BG_LIGHT.value
    )


def banner_progress_style() -> str:
    """Label/button rules for the banner's neutral "progress" mode."""
    is_dark = is_dark_theme()
    text_str = "white" if is_dark else "black"

    return f"""
    #banner QLabel {{ color: {text_str}; background: transparent; }}
    {banner_close_button_progress_style()}
    """


def boxed_label_style(is_large: bool = False) -> str:
    """Style used for boxed text labels, like file extensions and durations on item thumbnails."""
    font_size = 18 if is_large else 12
    return (
        "background-color: rgba(0, 0, 0, 192);"
        "color: #FFFFFF;"
        "font-family: Oxanium;"
        "font-weight: bold;"
        f"font-size: {font_size}px;"
        "border-radius: 3px;"
        "padding-top: 4px;"
        "padding-right: 1px;"
        "padding-bottom: 1px;"
        "padding-left: 1px;"
    )


def icon_button_style() -> str:
    """Style used for icon-only buttons, which draw no background even while pressed."""
    return "QPushButton { background: transparent; border: none; }"


def item_thumb_filename_style(is_selected: bool = False, is_placeholder: bool = False) -> str:
    """Style used for filename labels under item thumbnails, highlighted when selected."""
    if is_selected:
        return (
            "background-color: palette(highlight);"
            "color: palette(highlighted-text);"
            "font-size: 10px;"
            "padding-bottom: 1px;"
            "padding-left: 1px;"
            f"border-radius: {HALF_PAD}px;"
        )
    if is_placeholder:
        background = "rgba(255, 255, 255, 13)" if is_dark_theme() else "rgba(0, 0, 0, 34)"
        return (
            f"background-color: {background};"
            "font-size: 10px;"
            "padding-bottom: 1px;"
            "padding-left: 1px;"
            f"border-radius: {HALF_PAD}px;"
        )
    return "font-size: 10px; padding-left: 1px; padding-bottom: 1px;"


def box_selection_style() -> str:
    """Style for box selections.

    NOTE: This does not style Qt's `QRubberBand` widget as that doesn't respect stylesheets.
    This style is used for custom implemented plain QWidgets treated as box selections.
    """
    accent = Palette.accent()
    return (
        f"background-color: rgba({accent.red()}, {accent.green()}, {accent.blue()}, 64);"
        f"border: 1px solid {accent.name()};"
        f"border-radius: {INNER_RADIUS}px;"
    )


def item_thumb_faded_select_color() -> QColor:
    """Semi-transparent accent color used to fill selected item thumbnails."""
    color = Palette.accent()
    color.setHsl(color.hslHue(), color.hslSaturation(), max(color.lightness(), 127), 127)
    return color


def item_thumb_hover_color() -> QColor:
    """Lightened accent color for hovered item thumbnails and resize handles."""
    color = Palette.accent()
    color.setHsl(
        color.hslHue(),
        min(255, round(color.hslSaturation() * 1.25)),
        min(color.lightness() + 80, 255),
        color.alpha(),
    )
    return color


def banner_progress_chunk_color() -> QColor:
    """Fill color for the banner's custom-painted progress bar chunk."""
    chunk = Palette.accent_alt()
    return chunk


def header(string: str, level: int, color: str | None = None) -> str:
    """Wrap a string in HTML header tags.

    Args:
        string (str): The string to format.
        level (int): A value between 1 and 6 denoting the header level.
            For example, "1" will create <h1> tags, "6" will create <h6> tags, etc.
        color: Optional color string to pass as an inline HTML style.
    """
    if level < 1:
        level = 1
    elif level > 6:
        level = 6

    style_tag: str = ""
    if color is not None:
        style_tag = f" style='color: {color}'"

    return f"<h{level}{style_tag}>{string}</h{level}>"


def tag_colors(color_group: TagColorGroup | None) -> tuple[QColor, QColor, QColor, QColor]:
    """Return the primary, border, highlight, and text colors for a tag color group."""
    primary = QColor(
        color_group.primary
        if color_group
        else get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT)
    )
    border = get_tag_border_color(primary)
    highlight = get_tag_highlight_color(primary)
    text = get_tinted_tag_text_color(primary)

    if color_group and color_group.secondary:
        secondary = QColor(color_group.secondary)
        highlight, text = get_tag_highlight_color(secondary), secondary
        if color_group.color_border:
            border = secondary

    return primary, border, highlight, text


def capsule_colors(
    color_group: TagColorGroup | None,
) -> tuple[QColor, QColor | None, QColor, QColor]:
    """Return a Capsule's fill, border (only if the tag has one), highlight, and text colors."""
    if color_group is None:
        # Translucent, so tags without a color blend with whatever they sit on
        return _colorless_capsule_colors(QColor(48, 48, 52, 128))

    primary, border, highlight, text = tag_colors(color_group)
    has_border = bool(color_group.secondary and color_group.color_border)
    return primary, border if has_border else None, highlight, text


def control_capsule_colors() -> tuple[QColor, QColor | None, QColor, QColor]:
    """Return the colors for controls drawn like tags/capsules, for example special checkboxes."""
    return _colorless_capsule_colors(QColor(0, 0, 0, 128))


def _colorless_capsule_colors(dark_primary: QColor) -> tuple[QColor, None, QColor, QColor]:
    """Capsule colors with a fill for the dark theme, or translucent white for the light theme."""
    is_dark = QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
    primary = dark_primary if is_dark else QColor(255, 255, 255, 128)
    highlight = get_tag_highlight_color(primary)
    return primary, None, highlight, get_tag_text_color(primary, highlight)


def get_tag_border_color(primary_color: QColor) -> QColor:
    border_color: QColor = QColor(primary_color)
    border_color.setRed(min(border_color.red() + 20, 255))
    border_color.setGreen(min(border_color.green() + 20, 255))
    border_color.setBlue(min(border_color.blue() + 20, 255))

    return border_color


def get_tag_highlight_color(primary_color: QColor) -> QColor:
    highlight_color: QColor = QColor(primary_color)
    highlight_color = highlight_color.toHsl()
    highlight_color.setHsl(highlight_color.hue(), min(highlight_color.saturation(), 200), 225, 255)
    highlight_color = highlight_color.toRgb()

    return highlight_color


def get_tinted_tag_text_color(primary_color: QColor) -> QColor:
    """A tag's color darkened or lightened for contrast, then tinted by burning or screening it."""
    tag_text_darkness = 0.65  # Black blended with tag text color, for light background colors
    tag_text_lightness = 0.75  # White blended with tag text color, for dark background colors
    tag_text_tint = 0.5  # How much burning or screening tints the tag text

    fill = QColor(primary_color.red(), primary_color.green(), primary_color.blue())
    if primary_color.lightness() > 120:
        base = blend(fill, QColor(Qt.GlobalColor.black), tag_text_darkness)
        mode = burn
    else:
        base = blend(fill, QColor(Qt.GlobalColor.white), tag_text_lightness)
        mode = screen
    tinted = QColor(
        mode(base.red(), fill.red()),
        mode(base.green(), fill.green()),
        mode(base.blue(), fill.blue()),
    )
    return blend(base, tinted, tag_text_tint)


def get_tag_text_color(primary_color: QColor, highlight_color: QColor) -> QColor:
    if primary_color.lightness() > 120:
        text_color = QColor(primary_color)
        text_color = text_color.toHsl()
        text_color.setHsl(text_color.hue(), text_color.saturation(), 50, 255)
        return text_color.toRgb()
    else:
        return highlight_color


def button_style() -> str:
    """Style used for common QPushButtons."""
    return f"""
    QPushButton{{
        background-color: {ThemePalette.COLOR_BG.value};
        border-radius: {RADIUS}px;
        font-weight: 500;
        text-align: center;
        padding: 0px 12px;
    }}
    QPushButton::hover{{
        background-color: {ThemePalette.COLOR_HOVER.value};
        border-style: solid;
        border-width: 2px;
        border-color: {get_ui_color(ColorType.BORDER, UiColor.THEME_DARK)};
        padding: 0px 8px;
    }}
    QPushButton::pressed{{
        outline: none;
        background-color: palette(light);
        border-style: solid;
        border-width: 2px;
        border-color: {get_ui_color(ColorType.BORDER, UiColor.THEME_DARK)};
        padding: 0px 8px;
    }}
    QPushButton::focus{{
        outline: none;
        border: solid;
        border-width: 2px;
        border-color: rgba{Palette.accent().toTuple()};
        padding: 0px 8px;
    }}
    QPushButton::disabled{{
        background-color: {ThemePalette.COLOR_DISABLED_BG.value};
    }}
"""


def checkbox_style() -> str:
    """Style used for common QCheckBoxes."""
    return colored_checkbox_style(*tag_colors(None))


def radio_button_style() -> str:
    """Style used for common QRadioButtons."""
    return colored_radio_button_style(*tag_colors(None))


def colored_checkbox_style(
    primary_color: QColor,
    border_color: QColor,
    highlight_color: QColor,
    text_color: QColor,
) -> str:
    """Style used for QCheckBoxes."""
    return f"""
        QCheckBox{{
            background: rgba{primary_color.toTuple()};
            color: rgba{text_color.toTuple()};
            border-color: rgba{border_color.toTuple()};
            border-radius: {RADIUS}px;
            border-style: solid;
            border-width: 2px;
        }}
        QCheckBox::indicator{{
            width: 10px;
            height: 10px;
            border-radius: 2px;
            margin: 4px;
        }}
        QCheckBox::indicator:checked{{
            background: rgba{text_color.toTuple()};
        }}
        QCheckBox::hover{{
            border-color: rgba{highlight_color.toTuple()};
        }}
        QCheckBox::focus{{
            border-color: rgba{highlight_color.toTuple()};
            outline: none;
        }}
        """


def colored_radio_button_style(
    primary_color: QColor,
    border_color: QColor,
    highlight_color: QColor,
    text_color: QColor,
) -> str:
    return f"""
    QRadioButton{{
        background: rgba{primary_color.toTuple()};
        color: rgba{text_color.toTuple()};
        border-color: rgba{border_color.toTuple()};
        border-radius: {RADIUS}px;
        border-style: solid;
        border-width: 2px;
    }}
    QRadioButton::indicator{{
        width: 10px;
        height: 10px;
        border-radius: 2px;
        margin: 4px;
    }}
    QRadioButton::indicator:checked{{
        background: rgba{text_color.toTuple()};
    }}
    QRadioButton::hover{{
        border-color: rgba{highlight_color.toTuple()};
    }}
    QRadioButton::pressed{{
        background: rgba{border_color.toTuple()};
        color: rgba{primary_color.toTuple()};
        border-color: rgba{primary_color.toTuple()};
    }}
    QRadioButton::focus{{
        border-color: rgba{highlight_color.toTuple()};
        outline: none;
    }}
    """


def line_edit_style() -> str:
    """Style used for QLineEdits."""
    return f"""
    border: 1px solid {get_ui_color(ColorType.PRIMARY, UiColor.RED)};
    border-radius: 2px
    """


def properties_style() -> str:
    """Style used for small labels such as file properties."""
    label_bg_color = (
        ThemePalette.COLOR_BG_DARK.value
        if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
        else ThemePalette.COLOR_DARK_LABEL.value
    )

    return f"""
    background-color: {label_bg_color};
    color: #FFFFFF;
    font-family: Oxanium;
    font-weight: bold;
    font-size: 12px;
    border-radius: {INNER_RADIUS}px;
    padding-top: 4px;
    padding-right: 1px;
    padding-bottom: 1px;
    padding-left: 1px;
    """


def info_popover_style() -> str:
    """Style used for popovers shown by info buttons."""
    border_color = (
        "#404040"
        if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
        else "#808080"
    )
    return f"""
    #info_popover{{
        background: palette(window);
        border: 1px solid {border_color};
        border-radius: 6px;
        padding: 9px;
    }}
    """


def item_thumb_check_badge_style(size: int, icon: Path, checked_icon: Path) -> str:
    """Style used for checkable tag badges on item thumbnails, like Favorite and Archived."""
    return (
        f"QCheckBox::indicator{{width: {size}px;height: {size}px;}}"
        f'QCheckBox::indicator::unchecked{{image: url("{icon.as_posix()}")}}'
        f'QCheckBox::indicator::checked{{image: url("{checked_icon.as_posix()}")}}'
    )
