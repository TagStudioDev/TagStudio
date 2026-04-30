# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

"""Tests for the security caps applied to attacker-controlled XML reads."""

import struct
from pathlib import Path
from unittest.mock import patch

from pytestqt.qtbot import QtBot

from tagstudio.qt.previews.renderer import ThumbRenderer
from tagstudio.qt.ts_qt import QtDriver


def test_mdp_thumb_rejects_oversize_header(
    qtbot: QtBot, qt_driver: QtDriver, tmp_path: Path
):
    """A .mdp claiming a header larger than the cap is rejected before allocation."""
    qt_driver.settings.mdp_header_max_mb = 1
    renderer = ThumbRenderer(qt_driver)

    # Magic ("mdipack" + null) followed by <LLL> bin_header where bin_header[1]
    # is the declared XML header length. 10 MiB > 1 MiB cap.
    mdp = tmp_path / "test.mdp"
    declared = 10 * 1024 * 1024
    mdp.write_bytes(b"mdipack\x00" + struct.pack("<LLL", 0, declared, 0))

    with patch("tagstudio.qt.previews.renderer.ET.fromstring") as parse_spy:
        result = renderer._mdp_thumb(mdp)  # pyright: ignore[reportPrivateUsage]

    assert result is None
    parse_spy.assert_not_called()


def test_pdn_thumb_rejects_oversize_header(
    qtbot: QtBot, qt_driver: QtDriver, tmp_path: Path
):
    """A .pdn claiming a header larger than the cap is rejected before allocation."""
    qt_driver.settings.pdn_header_max_mb = 1
    renderer = ThumbRenderer(qt_driver)

    # Magic ("PDN3") followed by a 24-bit little-endian header_size. 10 MiB > 1 MiB cap.
    pdn = tmp_path / "test.pdn"
    declared = 10 * 1024 * 1024
    pdn.write_bytes(b"PDN3" + declared.to_bytes(3, "little"))

    with patch("tagstudio.qt.previews.renderer.ET.fromstring") as parse_spy:
        result = renderer._pdn_thumb(pdn)  # pyright: ignore[reportPrivateUsage]

    assert result is None
    parse_spy.assert_not_called()
