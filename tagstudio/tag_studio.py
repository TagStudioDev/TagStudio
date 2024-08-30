# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

"""TagStudio launcher."""

from src.core.ts_core import TagStudioCore
from src.cli.ts_cli import CliDriver  # type: ignore
from src.qt.ts_qt import QtDriver
import argparse
import traceback


def main() -> None:
    # appid = "cyanvoxel.tagstudio.9"
    # ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)

    # Parse arguments.
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    # Add an "open" argument as a library to open while starting.
    parser.add_argument(
        "-o",
        "--open",
        dest="open",
        type=str,
        help="Path to a TagStudio Library folder to open on start.",
    )
    # Add "config file"(-c) option to use as the config of the program.
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

    # Add "debug" argument to help debug the program.
    parser.add_argument(
        "--debug",
        dest="debug",
        action="store_true",
        help="Reveals additional internal data useful for debugging.",
    )
    # Add "ui" argument to determine the library to use?
    parser.add_argument(
        "--ui",
        dest="ui",
        type=str,
        help="User interface option for TagStudio. Options: qt, cli (Default: qt)",
    )
    # Add a "ci" argument to exit after successfully start-up
    parser.add_argument(
        "--ci",
        action=argparse.BooleanOptionalAction,
        help="Exit the application after checking it starts without any problem. Meant for CI check.",
    )
    # Parse all of the arguments
    args: argparse.Namespace = parser.parse_args()

    core: TagStudioCore = TagStudioCore()  # The TagStudio Core instance. UI agnostic.
    # TODO: Check if this is necessary:
    driver = None  # The UI driver instance.
    ui_name: str = "unknown"  # Display name for the UI, used in logs.

    #
    # Driver selection based on parameters.
    #
    #In case the driver is a Qt driver
    if args.ui and args.ui == "qt":
        # Run the TagStudio Qt driver
        driver = QtDriver(core, args)
        # Save UI name for later use(crash message)
        ui_name = "Qt"
    # In case the driver is a CLI(command line interface) driver
    elif args.ui and args.ui == "cli":
        # Run the TagStudio CLI driver
        driver = CliDriver(core, args)
        # Save UI name for later use(crash message)
        ui_name = "CLI"
    # In case UI was not specified
    else:
        # Run the TagStudio Qt driver by default
        driver = QtDriver(core, args)
        # Save UI name for later use(crash message)
        ui_name = "Qt"

    # Try to run the chosen frontend driver.
    try:
        driver.start()
    # TODO: Potentially remove the try except since "driver.start" has it covered?
    # In case of failure
    except Exception:
        traceback.print_exc()
        # Display a crash message.
        print(f"\nTagStudio Frontend ({ui_name}) Crashed! Press Enter to Continue...")
        # Wait for user input.
        input()


if __name__ == "__main__":
    main()
