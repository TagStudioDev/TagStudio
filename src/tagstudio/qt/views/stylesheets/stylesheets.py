# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication

from tagstudio.core.enums import Theme
from tagstudio.core.library.alchemy.enums import TagColorEnum
from tagstudio.core.library.alchemy.models import Tag
from tagstudio.qt.models.palette import ColorType, Palette, UiColor, get_tag_color, get_ui_color

# TODO: There's plenty of good opportunities here to consolidate similar styles.
# Work should be done to more closely use Qt's theming systems rather than override them.


def add_button_style() -> str:
    """Style used for tag-like "Add" buttons [+]."""
    return f"""
    QPushButton{{
        background: {get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT)};
        color: {get_tag_color(ColorType.TEXT, TagColorEnum.DEFAULT)};
        font-weight: 600;
        border-color: {get_tag_color(ColorType.BORDER, TagColorEnum.DEFAULT)};
        border-radius: 6px;
        border-style: solid;
        border-width: 2px;
        padding-right: 4px;
        padding-bottom: 2px;
        padding-left: 4px;
        font-size: 15px
    }}
    QPushButton::hover{{
        border-color: {get_tag_color(ColorType.LIGHT_ACCENT, TagColorEnum.DEFAULT)};
    }}
    QPushButton::pressed{{
        background: {get_tag_color(ColorType.LIGHT_ACCENT, TagColorEnum.DEFAULT)};
        color: {get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT)};
        border-color: {get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT)};
    }}
    QPushButton::focus{{
        border-color: {get_tag_color(ColorType.LIGHT_ACCENT, TagColorEnum.DEFAULT)};
        outline: none;
    }}
    """


def button_style() -> str:
    """Style used for common QPushButtons."""
    return f"""
    QPushButton{{
        background-color: {Theme.COLOR_BG.value};
        border-radius: 6px;
        font-weight: 500;
        text-align: center;
        padding: 0px 12px;
    }}
    QPushButton::hover{{
        background-color: {Theme.COLOR_HOVER.value};
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
        border-color: {Palette.accent()};
        padding: 0px 8px;
    }}
    QPushButton::disabled{{
        background-color: {Theme.COLOR_DISABLED_BG.value};
    }}
"""


def line_edit_style_main() -> str:
    """Style used for common QLineEdits."""
    bg_color = (
        Theme.COLOR_BG_DARK.value
        if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
        else Theme.COLOR_BG_LIGHT.value
    )

    return f"""
    QLineEdit{{
        background: {bg_color};
        border-radius: 6px;
        font-weight: 500;
        text-align: center;
        padding: 0px 4px;
    }}
    QLineEdit::hover{{
        border-style: solid;
        border-width: 2px;
        border-color: {get_ui_color(ColorType.BORDER, UiColor.THEME_DARK)};
        padding: 0px 2px;
    }}
    QLineEdit::focus{{
        border-style: solid;
        border-width: 2px;
        border-color: {Palette.accent()};
        padding: 0px 2px;
    }}
    QLineEdit::disabled{{
        background-color: {Theme.COLOR_DISABLED_BG.value};
    }}
"""


def checkbox_style() -> str:
    """Style used for QCheckBoxes."""
    primary_color = QColor(get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT))
    border_color = get_tag_border_color(primary_color)
    highlight_color = get_tag_highlight_color(primary_color)
    text_color: QColor = get_tag_text_color(primary_color, highlight_color)
    return f"""
    QCheckBox{{
        background: rgba{primary_color.toTuple()};
        color: rgba{text_color.toTuple()};
        border-color: rgba{border_color.toTuple()};
        border-radius: 6px;
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
    text_color: QColor,
    border_color: QColor,
    highlight_color: QColor,
) -> str:
    return f"""
    QRadioButton{{
        background: rgba{primary_color.toTuple()};
        color: rgba{text_color.toTuple()};
        border-color: rgba{border_color.toTuple()};
        border-radius: 6px;
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


def color_swatch_style(
    primary_color: QColor,
    text_color: QColor,
    border_color: QColor,
    highlight_color: QColor,
    bottom_color: QColor | None = None,
) -> str:
    """A style used for color swatches (aka special QRadioButtons)."""
    bottom_color_str: str = (
        f"border-bottom-color: rgba{bottom_color.toTuple()};" if bottom_color else ""
    )

    return f"""
    QRadioButton{{
        background: rgba{primary_color.toTuple()};
        color: rgba{text_color.toTuple()};
        border-color: rgba{border_color.toTuple()};
        {bottom_color_str}
        border-radius: 3px;
        border-style: solid;
        border-width: 2px;
    }}
    QRadioButton::indicator{{
        width: 12px;
        height: 12px;
        border-radius: 1px;
        margin: 4px;
    }}
    QRadioButton::indicator:checked{{
        background: rgba{text_color.toTuple()};
    }}
    QRadioButton::hover{{
        border-color: rgba{highlight_color.toTuple()};
    }}
    QRadioButton::focus{{
        outline-style: solid;
        outline-width: 2px;
        outline-radius: 3px;
        outline-color: rgba{highlight_color.toTuple()};
    }}
    """


def container_style() -> str:
    """Style used for field containers."""
    return f"""
    QWidget#fieldContainer{{
        border-radius: 4px;
    }}
    QWidget#fieldContainer::hover{{
        background-color: {Theme.COLOR_HOVER.value};
    }}
    QWidget#fieldContainer::pressed{{
        background-color: {Theme.COLOR_PRESSED.value};
    }}
    """


def form_content_style() -> str:
    return f"""
    QLabel{{
        background-color: {
        Theme.COLOR_BG.value
        if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
        else Theme.COLOR_BG_LIGHT.value
    };
        border-radius: 3px;
        font-weight: 500;
        padding: 1px;
    }}
    """


def line_edit_style() -> str:
    """Style used for QLineEdits."""
    return f"""
    border: 1px solid {get_ui_color(ColorType.PRIMARY, UiColor.RED)};
    border-radius: 2px
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
        border-radius: 6px;
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


def properties_style() -> str:
    """Style used for small labels such as file properties."""
    label_bg_color = (
        Theme.COLOR_BG_DARK.value
        if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
        else Theme.COLOR_DARK_LABEL.value
    )

    return f"""
    background-color: {label_bg_color};
    color: #FFFFFF;
    font-family: Oxanium;
    font-weight: bold;
    font-size: 12px;
    border-radius: 3px;
    padding-top: 4px;
    padding-right: 1px;
    padding-bottom: 1px;
    padding-left: 1px;
    """


def tag_style(
    primary_color: QColor,
    text_color: QColor,
    border_color: QColor,
    highlight_color: QColor,
    border_style: str = "solid",
) -> str:
    """Style used for TagWidgets."""
    return f"""
    QPushButton{{
        background: rgba{primary_color.toTuple()};
        color: rgba{text_color.toTuple()};
        font-weight: 600;
        border-color: rgba{border_color.toTuple()};
        border-radius: 6px;
        border-style: {border_style};
        border-width: 2px;
        font-size: 13px;
        padding-right: 4px;
        padding-left: 4px;
    }}
    QPushButton::hover{{
        border-color: rgba{highlight_color.toTuple()};
    }}
    QPushButton::pressed{{
        background: rgba{highlight_color.toTuple()};
        color: rgba{primary_color.toTuple()};
        border-color: rgba{primary_color.toTuple()};
    }}
    QPushButton::focus{{
        outline: none;
        border-width: 3px;
        border-color: rgba{text_color.toTuple()};
    }}
    """


def tag_remove_button_style(
    primary_color: QColor, text_color: QColor, border_color: QColor, highlight_color: QColor
) -> str:
    """Style used for "Remove" buttons on TagWidgets [-]."""
    return f"""
    QPushButton{{
        color: rgba{primary_color.toTuple()};
        background: rgba{text_color.toTuple()};
        font-weight: 800;
        border-radius: 5px;
        border-width: 4;
        border-color: rgba(0,0,0,0);
        padding-bottom: 4px;
        font-size: 14px
    }}
    QPushButton::hover{{
        background: rgba{primary_color.toTuple()};
        color: rgba{text_color.toTuple()};
        border-color: rgba{highlight_color.toTuple()};
        border-width: 2;
        border-radius: 6px;
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


def widget_underline_style() -> str:
    return f"""
        background: {Palette.accent()};
        border-radius: 2px;
    """


def title_line_edit_style() -> str:
    """Used to mimic an H3-like header style inside a QLineEdit."""
    return """
    font-weight: bold;
    font-size: 16px;
    """


def inset_container_style(object_name: str = "") -> str:
    """Used for darkened inset areas."""
    bg_color = (
        Theme.COLOR_BG_DARK.value
        if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
        else Theme.COLOR_BG_LIGHT.value
    )

    return f"""
    QWidget{"#" + object_name if object_name else ""}{{
        background: {bg_color};
        border-radius: 6px;
        }}
    """


# TODO: Combine the autofill styles into one method?
def autofill_scroll_top_style(object_name: str = "") -> str:
    """Used autofill lists positioned on top of line edits."""
    bg_color = (
        Theme.COLOR_BG_DARK.value
        if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
        else Theme.COLOR_BG_LIGHT.value
    )

    return f"""
    QWidget{"#" + object_name if object_name else ""}{{
        background: {bg_color};
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        border: none;
        }}
    """


def autofill_scroll_top_focus_style(object_name: str = "") -> str:
    """Used autofill lists positioned on top of line edits."""
    bg_color = (
        Theme.COLOR_BG_DARK.value
        if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
        else Theme.COLOR_BG_LIGHT.value
    )

    return f"""
    QWidget{"#" + object_name if object_name else ""}{{
        background: {bg_color};
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        border: solid;
        border-width: 2px 2px 0px 2px;
        border-color: {Palette.accent()};
        }}
    """


def autofill_line_edit_style() -> str:
    """Used for QLineEdits."""
    bg_color = (
        Theme.COLOR_BG_DARK.value
        if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
        else Theme.COLOR_BG_LIGHT.value
    )

    return f"""
    QLineEdit{{
        background: {bg_color};
        border-radius: 6px;
        padding: 3px 6px;
        }}
    QLineEdit::focus{{
        padding: 4px 4px;
        border: solid;
        border-width: 2px;
        border-color: {Palette.accent()};
        }}
    """


def autofill_line_edit_top_style() -> str:
    """Used for QLineEdits when there's a top autofill section present."""
    bg_color = (
        Theme.COLOR_BG_DARK.value
        if QGuiApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark
        else Theme.COLOR_BG_LIGHT.value
    )

    return f"""
    QLineEdit{{
        background: {bg_color};
        border-top-left-radius: 0px;
        border-top-right-radius: 0px;
        border-bottom-left-radius: 6px;
        border-bottom-right-radius: 6px;
        padding: 0px 0px 2px 6px;
        }}
    QLineEdit::focus{{
        padding: 4px 4px;
        border: solid;
        border-width: 0px 2px 2px 2px;
        border-color: {Palette.accent()};
        }}
    """


def preview_warning_style() -> str:
    return f"""
    QWidget#ffmpeg_widget {{
        background: {get_ui_color(ColorType.DARK_ACCENT, UiColor.RED)};
        border-radius: 6px;
        }}
    """


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


def get_tag_primary_color(tag: Tag) -> QColor:
    primary_color = QColor(
        get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT)
        if not tag.color
        else tag.color.primary
    )

    return primary_color


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


def get_tag_text_color(primary_color: QColor, highlight_color: QColor) -> QColor:
    if primary_color.lightness() > 120:
        text_color = QColor(primary_color)
        text_color = text_color.toHsl()
        text_color.setHsl(text_color.hue(), text_color.saturation(), 50, 255)
        return text_color.toRgb()
    else:
        return highlight_color
