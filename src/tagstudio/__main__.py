#!/usr/bin/env python3
# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


"""TagStudio launcher."""

import argparse
import sys
import traceback

import structlog

from tagstudio.core.constants import BUILD_TYPE, VERSION
from tagstudio.i18n.translations import Translations
from tagstudio.qt.qt_driver import QtDriver

logger = structlog.get_logger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o",
        "--open",
        dest="open",
        type=str,
        help="Path to a TagStudio Library folder to open on start.",
    )
    parser.add_argument(
        "-s",
        "--settings-file",
        dest="settings_file",
        type=str,
        help="Path to a TagStudio .toml global settings file to use.",
    )
    parser.add_argument(
        "-c",
        "--cache-file",
        dest="cache_file",
        type=str,
        help="Path to a TagStudio .ini or .plist cache file to use.",
    )
    parser.add_argument(
        "--debug",
        dest="debug",
        action="store_true",
        help="Reveals additional internal data useful for debugging.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        help="Displays TagStudio version information.",
        version=f"TagStudio v{VERSION} {Translations[BUILD_TYPE] if BUILD_TYPE else ''}",
    )
    args = parser.parse_args()

    driver = QtDriver(args)
    ui_name = "Qt"

    # Run the chosen frontend driver.
    try:
        driver.start()
    except Exception:
        traceback.print_exc()
        logger.info(f"\nTagStudio Frontend ({ui_name}) Crashed! Press Enter to Continue...")
        input()


if __name__ == "__main__":
    sys.exit(main())
