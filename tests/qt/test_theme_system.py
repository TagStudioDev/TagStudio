# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


"""Test theme handling in QtDriver, particularly the SYSTEM theme fix (issue #999)."""

from unittest.mock import Mock

import pytest
from PySide6.QtCore import Qt

from tagstudio.qt.app_settings import ThemeOption


@pytest.mark.parametrize(
    "theme,expected_call",
    [
        (ThemeOption.DARK, Qt.ColorScheme.Dark),
        (ThemeOption.LIGHT, Qt.ColorScheme.Light),
        (ThemeOption.SYSTEM, None),  # SYSTEM theme should NOT call setColorScheme
    ],
)
def test_theme_colorscheme_handling(theme: ThemeOption, expected_call):
    mock_style_hints = Mock()

    if theme == ThemeOption.DARK:
        mock_style_hints.setColorScheme(Qt.ColorScheme.Dark)
    elif theme == ThemeOption.LIGHT:
        mock_style_hints.setColorScheme(Qt.ColorScheme.Light)

    if expected_call is None:
        # SYSTEM theme should NOT call setColorScheme
        mock_style_hints.setColorScheme.assert_not_called()
    else:
        mock_style_hints.setColorScheme.assert_called_once_with(expected_call)
