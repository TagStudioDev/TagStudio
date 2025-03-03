#!/usr/bin/env python
# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

"""TagStudio launcher."""

import argparse
import logging
import traceback

import structlog
from src.qt.ts_qt import QtDriver

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)


def main():
    # appid = "cyanvoxel.tagstudio.9"
    # ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)

    # Parse arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o",
        "--open",
        dest="open",
        type=str,
        help="Path to a TagStudio Library folder to open on start.",
    )
    parser.add_argument(
        "-c",
        "--config-file",
        dest="config_file",
        type=str,
        help="Path to a TagStudio .ini or .plist config file to use.",
    )

    # parser.add_argument('--browse', dest='browse', action='store_true',
    #                     help='Jumps to entry browsing on startup.')
    # parser.add_argument('--external_preview', dest='external_preview', action='store_true',
    #                     help='Outputs current preview thumbnail to a live-updating file.')
    parser.add_argument(
        "--debug",
        dest="debug",
        action="store_true",
        help="Reveals additional internal data useful for debugging.",
    )
    parser.add_argument(
        "--ui",
        dest="ui",
        type=str,
        help="User interface option for TagStudio. Options: qt, cli (Default: qt)",
    )
    args = parser.parse_args()
    from src.core.library import alchemy as backend

    driver = QtDriver(backend, args)
    ui_name = "Qt"

    # Run the chosen frontend driver.
    try:
        driver.start()
    except Exception:
        traceback.print_exc()
        logging.info(f"\nTagStudio Frontend ({ui_name}) Crashed! Press Enter to Continue...")
        input()


if __name__ == "__main__":
    main()
