from pathlib import Path

import toml
from pydantic import BaseModel, Field


# NOTE: pydantic also has a BaseSettings class (from pydantic-settings) that allows any settings
# properties to be overwritten with environment variables. as tagstudio is not currently using
# environment variables, i did not base it on that, but that may be useful in the future.
class TSSettings(BaseModel):
    dark_mode: bool = Field(default=False)
    language: str = Field(default="en-US")

    # settings from the old SettingItem enum
    open_last_loaded_on_startup: bool = Field(default=False)
    show_library_list: bool = Field(default=True)
    autoplay: bool = Field(default=False)
    show_filenames_in_grid: bool = Field(default=False)

    filename: str = Field()

    @staticmethod
    def read_settings(path: Path | str, **kwargs) -> "TSSettings":
        settings_data: dict[str, any] = dict()
        if path.exists():
            with open(path, "rb") as file:
                filecontents = file.read()
                if len(filecontents.strip()) != 0:
                    settings_data = toml.loads(filecontents.decode("utf-8"))

        settings_data["filename"] = str(path)
        settings = TSSettings(**settings_data)
        return settings

    def to_dict(self) -> dict[str, any]:
        d = dict[str, any]()
        for prop_name, prop_value in self:
            d[prop_name] = prop_value

        return d

    def save(self, path: Path | str | None = None) -> None:
        if isinstance(path, str):
            path = Path(path)

        if path is None:
            path = self.filename
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            toml.dump(self.to_dict(), f)
