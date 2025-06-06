# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import platform
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import override

import structlog
import toml
from pydantic import BaseModel, Field

from tagstudio.core.enums import ShowFilepathOption, TagClickActionOption

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
    tag_click_action: TagClickActionOption = Field(default=TagClickActionOption.DEFAULT)

    date_format: str = Field(default="%x")
    hour_format: bool = Field(default=True)
    zero_padding: bool = Field(default=True)

    loaded_from: Path = Field(default=DEFAULT_GLOBAL_SETTINGS_PATH, exclude=True)

    @staticmethod
    def read_settings(path: Path = DEFAULT_GLOBAL_SETTINGS_PATH) -> "GlobalSettings":
        if path.exists():
            with open(path) as file:
                filecontents = file.read()
                if len(filecontents.strip()) != 0:
                    logger.info("[Settings] Reading Global Settings File", path=path)
                    settings_data = toml.loads(filecontents)
                    settings = GlobalSettings(**settings_data, loaded_from=path)
                    return settings

        return GlobalSettings(loaded_from=path)

    def save(self, path: Path | None = None) -> None:
        if path is None:
            path = self.loaded_from
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            toml.dump(self.model_dump(), f, encoder=TomlEnumEncoder())

    @property
    def datetime_format(self) -> str:
        date_format = self.date_format
        is_24h = self.hour_format
        hour_format = "%H:%M:%S" if is_24h else "%I:%M:%S %p"
        zero_padding = self.zero_padding
        zero_padding_symbol = ""

        if not zero_padding:
            zero_padding_symbol = "#" if platform.system() == "Windows" else "-"
            date_format = date_format.replace("%d", f"%{zero_padding_symbol}d").replace(
                "%m", f"%{zero_padding_symbol}m"
            )
            hour_format = hour_format.replace("%H", f"%{zero_padding_symbol}H").replace(
                "%I", f"%{zero_padding_symbol}I"
            )
        return f"{date_format}, {hour_format}"

    def format_datetime(self, dt: datetime) -> str:
        return datetime.strftime(dt, self.datetime_format)
