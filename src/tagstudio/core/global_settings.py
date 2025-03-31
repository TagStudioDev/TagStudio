# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import platform
from enum import Enum
from pathlib import Path
from typing import override

import structlog
import toml
from pydantic import BaseModel, Field

from tagstudio.core.enums import ShowFilepathOption

if platform.system() == "Windows":
    DEFAULT_GLOBAL_SETTINGS_PATH = (
        Path.home() / "Appdata" / "Roaming" / "TagStudio" / "settings.toml"
    )
else:
    DEFAULT_GLOBAL_SETTINGS_PATH = Path.home() / ".config" / "TagStudio" / "settings.toml"

logger = structlog.get_logger(__name__)


class TomlEnumEncoder(toml.TomlEncoder):
    @override
    def dump_value(self, v):
        if isinstance(v, Enum):
            return super().dump_value(v.value)
        return super().dump_value(v)


class Theme(Enum):
    DARK = 0
    LIGHT = 1
    SYSTEM = 2
    DEFAULT = SYSTEM


# NOTE: pydantic also has a BaseSettings class (from pydantic-settings) that allows any settings
# properties to be overwritten with environment variables. as tagstudio is not currently using
# environment variables, i did not base it on that, but that may be useful in the future.
class GlobalSettings(BaseModel):
    language: str = Field(default="en")
    open_last_loaded_on_startup: bool = Field(default=True)
    autoplay: bool = Field(default=True)
    loop: bool = Field(default=True)
    show_filenames_in_grid: bool = Field(default=True)
    page_size: int = Field(default=100)
    show_filepath: ShowFilepathOption = Field(default=ShowFilepathOption.DEFAULT)
    theme: Theme = Field(default=Theme.SYSTEM)

    @staticmethod
    def read_settings(path: Path = DEFAULT_GLOBAL_SETTINGS_PATH) -> "GlobalSettings":
        if path.exists():
            with open(path) as file:
                filecontents = file.read()
                if len(filecontents.strip()) != 0:
                    logger.info("[Settings] Reading Global Settings File", path=path)
                    settings_data = toml.loads(filecontents)
                    settings = GlobalSettings(**settings_data)
                    return settings

        return GlobalSettings()

    def save(self, path: Path = DEFAULT_GLOBAL_SETTINGS_PATH) -> None:
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            toml.dump(dict(self), f, encoder=TomlEnumEncoder())
