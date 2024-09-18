from collections.abc import Callable

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from .qt_logger import logger

theme_update_hooks: list[Callable[[], None]] = []
"List of callables that will be called when any theme is changed."


def _update_theme_hooks() -> None:
    """Update all theme hooks by calling each hook in the list."""
    for hook in theme_update_hooks:
        try:
            hook()
        except Exception as e:
            logger.error(e)


def _load_palette_from_file(file_path: str, default_palette: QPalette) -> QPalette:
    """Load a palette from a file and update the default palette with the loaded colors.

    The file should be in the INI format and should have the following format:

    [ColorRoleName]
    ColorGroupName = Color

    ColorRoleName is the name of the color role (e.g. Window, Button, etc.)
    ColorGroupName is the name of the color group (e.g. Active, Inactive, Disabled, etc.)
    Color is the color value in the QColor supported format (e.g. #RRGGBB, blue, etc.)

    Args:
        file_path (str): The path to the file containing color information.
        default_palette (QPalette): The default palette to be updated with the colors.

    Returns:
        QPalette: The updated palette based on the colors specified in the file.
    """
    theme = QSettings(file_path, QSettings.Format.IniFormat, QApplication.instance())

    color_groups = (
        QPalette.ColorGroup.Active,
        QPalette.ColorGroup.Inactive,
        QPalette.ColorGroup.Disabled,
    )

    pal = default_palette

    for role in list(QPalette.ColorRole)[:-1]:  # remove last color role (NColorRoles)
        for group in color_groups:
            value: str | None = theme.value(f"{role.name}/{group.name}", None, str)  # type: ignore
            if value is not None and QColor.isValidColor(value):
                pal.setColor(group, role, QColor(value))

    return pal


def _save_palette_to_file(file_path: str, palette: QPalette) -> None:
    """Save the given palette colors to a file in INI format, if the color is not default.

    If no color is changed, the file won't be created or changed.

    The file will be in the INI format and will have the following format:

    [ColorRoleName]
    ColorGroupName = Color

    ColorRoleName is the name of the color role (e.g. Window, Button, etc.)
    ColorGroupName is the name of the color group (e.g. Active, Inactive, Disabled, etc.)
    Color is the color value in the RgbHex (#RRGGBB) or ArgbHex (#AARRGGBB) format.

    Args:
        file_path (str): The path to the file where the palette will be saved.
        palette (QPalette): The palette to be saved.

    Returns:
        None
    """
    theme = QSettings(file_path, QSettings.Format.IniFormat, QApplication.instance())

    color_groups = (
        QPalette.ColorGroup.Active,
        QPalette.ColorGroup.Inactive,
        QPalette.ColorGroup.Disabled,
    )
    default_pal = QPalette()

    for role in list(QPalette.ColorRole)[:-1]:  # remove last color role (NColorRoles)
        theme.beginGroup(role.name)
        for group in color_groups:
            if default_pal.color(group, role) != palette.color(group, role):
                theme.setValue(group.name, palette.color(group, role).name())
        theme.endGroup()


def update_palette() -> None:
    """Update the application palette based on the settings.

    This function retrieves the dark mode value and theme file paths from the settings.
    It then determines the dark mode status and loads the appropriate palette from the theme files.
    Finally, it sets the application palette and updates the theme hooks.

    Returns:
        None
    """
    # region XXX: temporarily getting settings data from QApplication.property("driver")
    instance = QApplication.instance()
    if instance is None:
        return
    driver = instance.property("driver")
    if driver is None:
        return
    settings: QSettings = driver.settings

    settings.beginGroup("Appearance")
    dark_mode_value: str = settings.value("DarkMode", -1)  # type: ignore
    dark_theme_file: str | None = settings.value("DarkThemeFile", None)  # type: ignore
    light_theme_file: str | None = settings.value("LightThemeFile", None)  # type: ignore
    settings.endGroup()
    # endregion

    # TODO: get values of following from settings.
    # dark_mode: bool | Literal[-1]
    # "True: Dark mode. False: Light mode. -1: System mode."
    # dark_theme_file: str | None
    # "Path to the dark theme file."
    # light_theme_file: str | None
    # "Path to the light theme file."

    true_values = ("1", "yes", "true", "on")
    false_values = ("0", "no", "false", "off")

    if dark_mode_value.lower() in ("1", "yes", "true", "on"):
        dark_mode = True
    elif dark_mode_value.lower() in ("0", "no", "false", "off"):
        dark_mode = False
    elif dark_mode_value == "-1":
        dark_mode = -1
    else:
        logger.error(f"""Invalid value for DarkMode: {dark_mode_value}. Defaulting to -1.
                     possible values: {true_values=}, {false_values=}, system=-1""")
        dark_mode = -1

    if dark_mode == -1:
        dark_mode = QApplication.styleHints().colorScheme() is Qt.ColorScheme.Dark

    if dark_mode:
        if dark_theme_file is None:
            palette = QPalette()  # default palette
        else:
            palette = _load_palette_from_file(dark_theme_file, QPalette())
    else:
        if light_theme_file is None:
            palette = QPalette()  # default palette
        else:
            palette = _load_palette_from_file(light_theme_file, QPalette())

    QApplication.setPalette(palette)

    _update_theme_hooks()


def save_current_palette(theme_file: str) -> None:
    _save_palette_to_file(theme_file, QApplication.palette())


# the following signal emits when system theme (Dark, Light) changes (Not accent color).
QApplication.styleHints().colorSchemeChanged.connect(update_palette)
