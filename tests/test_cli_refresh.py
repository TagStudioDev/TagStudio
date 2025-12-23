# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

"""Tests for CLI refresh functionality."""

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

CWD = Path(__file__).parent
sys.path.insert(0, str(CWD.parent))

from tagstudio.core.cli_driver import CliDriver


def test_cli_driver_refresh_nonexistent_library():
    """Test that refresh fails gracefully with a nonexistent library path."""
    driver = CliDriver()
    result = driver.refresh_library("/nonexistent/path/that/does/not/exist")
    assert result == 1, "Should return exit code 1 for nonexistent library"


def test_cli_driver_refresh_invalid_library():
    """Test that refresh fails gracefully with a directory that's not a TagStudio library."""
    with TemporaryDirectory() as tmpdir:
        driver = CliDriver()
        result = driver.refresh_library(tmpdir)
        # Should fail because it's not a TagStudio library (no .TagStudio folder)
        assert result == 1, "Should return exit code 1 for invalid/unopenable library"


def test_cli_driver_init():
    """Test that CliDriver initializes correctly."""
    driver = CliDriver()
    assert driver.lib is not None, "CLI driver should have a Library instance"
    assert hasattr(driver, "refresh_library"), "CLI driver should have refresh_library method"
