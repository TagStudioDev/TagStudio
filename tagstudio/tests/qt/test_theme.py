from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from src.qt.theme import _load_palette_from_file, _save_palette_to_file, update_palette


def test_save_palette_to_file(tmp_path: Path):
    file = tmp_path / "test_tagstudio_theme.txt"

    pal = QPalette()
    pal.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Button, QColor("#6E4BCE"))

    _save_palette_to_file(str(file), pal)

    with open(file) as f:
        data = f.read()
        assert data

    expacted_lines = (
        "[Button]",
        "Active=#6e4bce",
    )

    for saved, expected in zip(data.splitlines(), expacted_lines):
        assert saved == expected


def test_load_palette_from_file(tmp_path: Path):
    file = tmp_path / "test_tagstudio_theme_2.txt"

    file.write_text("[Button]\nActive=invalid color\n[Window]\nDisabled=#ff0000\nActive=blue")

    pal = _load_palette_from_file(str(file), QPalette())

    # check if Active Button color is default
    active = QPalette.ColorGroup.Active
    button = QPalette.ColorRole.Button
    assert pal.color(active, button) == QPalette().color(active, button)

    # check if Disabled Window color is #ff0000
    assert pal.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Window) == QColor("#ff0000")
    # check if Active Window color is #0000ff
    assert pal.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Window) == QColor("#0000ff")


def test_update_palette(tmp_path: Path) -> None:
    settings_file = tmp_path / "test_tagstudio_settings.ini"
    dark_theme_file = tmp_path / "test_tagstudio_dark_theme.txt"
    light_theme_file = tmp_path / "test_tagstudio_light_theme.txt"

    dark_theme_file.write_text("[Window]\nActive=#1f153a\n")
    light_theme_file.write_text("[Window]\nActive=#6e4bce\n")

    settings_file.write_text(
        "\n".join(
            (
                "[Appearance]",
                "DarkMode=true",
                f"DarkThemeFile={dark_theme_file}".replace("\\", "\\\\"),
                f"LightThemeFile={light_theme_file}".replace("\\", "\\\\"),
            )
        )
    )

    # region NOTE: temporary solution for test by making fake driver to use QSettings
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])

    class Driver:
        settings = QSettings(str(settings_file), QSettings.Format.IniFormat, app)

    app.setProperty("driver", Driver)
    # endregion

    update_palette()

    value = QApplication.palette().color(QPalette.ColorGroup.Active, QPalette.ColorRole.Window)
    expected = QColor("#1f153a")
    assert value == expected, f"{value.name()} != {expected.name()}"

    Driver.settings.setValue("Appearance/DarkMode", "false")

    # emiting colorSchemeChanged just to make sure the palette updates by colorSchemeChanged signal
    QApplication.styleHints().colorSchemeChanged.emit(Qt.ColorScheme.Dark)

    value = QApplication.palette().color(QPalette.ColorGroup.Active, QPalette.ColorRole.Window)
    expected = QColor("#6e4bce")
    assert value == expected, f"{value.name()} != {expected.name()}"
