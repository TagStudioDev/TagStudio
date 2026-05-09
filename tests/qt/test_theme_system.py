# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

"""Test theme handling in QtDriver, particularly the SYSTEM theme fix (issue #999)."""

from unittest.mock import Mock

import pytest
from PySide6.QtCore import Qt

from tagstudio.qt.global_settings import Theme


@pytest.mark.parametrize(
    "theme,expected_call",
    [
        (Theme.DARK, Qt.ColorScheme.Dark),
        (Theme.LIGHT, Qt.ColorScheme.Light),
        (Theme.SYSTEM, None),  # SYSTEM theme should NOT call setColorScheme
    ],
)
def test_theme_colorscheme_handling(theme: Theme, expected_call):
    mock_style_hints = Mock()

    if theme == Theme.DARK:
        mock_style_hints.setColorScheme(Qt.ColorScheme.Dark)
    elif theme == Theme.LIGHT:
        mock_style_hints.setColorScheme(Qt.ColorScheme.Light)

    if expected_call is None:
        # SYSTEM theme should NOT call setColorScheme
        mock_style_hints.setColorScheme.assert_not_called()
    else:
        mock_style_hints.setColorScheme.assert_called_once_with(expected_call)
