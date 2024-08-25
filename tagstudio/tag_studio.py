# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

"""TagStudio launcher."""

from src.core.ts_core import TagStudioCore
from src.cli.ts_cli import CliDriver  # type: ignore
from src.qt.ts_qt import QtDriver
from args import TagStudioArgs, parser
from tagstudio.logger import tag_studio_log


def main():
    # appid = "cyanvoxel.tagstudio.9"
    # ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)

    args = parser.parse_args(namespace=TagStudioArgs)

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
    except Exception as e:
        msg = f"TagStudio Frontend ({ui_name}) Crashed! Press Enter to Continue..."
        tag_studio_log.error(e)
        print(msg)
        input()


if __name__ == "__main__":
    main()
