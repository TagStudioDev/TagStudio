from pathlib import Path

import toml
from pydantic import BaseModel, Field


# NOTE: pydantic also has a BaseSettings class (from pydantic-settings) that allows any settings
# properties to be overwritten with environment variables. as tagstudio is not currently using
# environment variables, i did not base it on that, but that may be useful in the future.
class TSSettings(BaseModel):
    dark_mode: bool = Field(default=False)
    language: str = Field(default="en")

    # settings from the old SettingItem enum
    open_last_loaded_on_startup: bool = Field(default=False)
    show_library_list: bool = Field(default=True)
    autoplay: bool = Field(default=False)
    show_filenames_in_grid: bool = Field(default=False)

    filename: str = Field()

    @staticmethod
    def read_settings(path: Path | str) -> "TSSettings":
        path_value = Path(path)
        if path_value.exists():
            with open(path) as file:
                filecontents = file.read()
                if len(filecontents.strip()) != 0:
                    settings_data = toml.loads(filecontents)
                    return TSSettings(**settings_data)

        return TSSettings(filename=str(path))

    def save(self, path: Path | str | None = None) -> None:
        path_value: Path = Path(path) if isinstance(path, str) else Path(self.filename)
        if path_value == "":
            pass
            # settings were probably opened for an in-memory library - save to preferences table

        if not path_value.parent.exists():
            path_value.parent.mkdir(parents=True, exist_ok=True)

        with open(path_value, "w") as f:
            toml.dump(dict(self), f)
