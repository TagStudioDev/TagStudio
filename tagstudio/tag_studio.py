# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

"""TagStudio launcher."""

from src.core.ts_core import TagStudioCore
from src.cli.ts_cli import CliDriver
from src.qt.ts_qt import QtDriver
import argparse
import traceback


def main():
    # appid = "cyanvoxel.tagstudio.9"
    # ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)

    # Parse arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--open",
        dest="open",
        type=str,
        help="Path to a TagStudio Library folder to open on start.",
    )
    parser.add_argument(
        "-o",
        dest="open",
        type=str,
        help="Path to a TagStudio Library folder to open on start.",
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

    core = TagStudioCore()  # The TagStudio Core instance. UI agnostic.
    driver = None  # The UI driver instance.
    ui_name: str = "unknown"  # Display name for the UI, used in logs.

    # Driver selection based on parameters.
    if args.ui and args.ui == "qt":
        driver = QtDriver(core, args)
        ui_name = "Qt"
    elif args.ui and args.ui == "cli":
        driver = CliDriver(core, args)
        ui_name = "CLI"
    else:
        driver = QtDriver(core, args)
        ui_name = "Qt"

    # Run the chosen frontend driver.
    try:
        driver.start()
    except Exception:
        traceback.print_exc()
        print(f"\nTagStudio Frontend ({ui_name}) Crashed! Press Enter to Continue...")
        input()


if __name__ == "__main__":
    main()
