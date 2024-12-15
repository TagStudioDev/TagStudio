from pathlib import Path

import toml
from pydantic import BaseModel, Field


# NOTE: pydantic also has a BaseSettings class (from pydantic-settings) that allows any settings
# properties to be overwritten with environment variables. as tagstudio is not currently using
# environment variables, i did not base it on that, but that may be useful in the future.
class TSSettings(BaseModel):
    dark_mode: bool = Field(default=False)
    language: str = Field(default="en-US")

    @staticmethod
    def read_settings(path: Path | str, **kwargs) -> "TSSettings":
        # library = kwargs.get("library")
        settings_data: dict[str, any] = dict()
        if path.exists():
            with open(path, "rb").read() as filecontents:
                if len(filecontents.strip()) != 0:
                    settings_data = toml.loads(filecontents.decode("utf-8"))

        # if library: #TODO: add library-specific settings
        #    lib_settings_path = Path(library.folder / "settings.toml")
        #    lib_settings_data: dict[str, any]
        #    if lib_settings_path.exists:
        #        with open(lib_settings_path, "rb") as filedata:
        #            lib_settings_data = tomllib.load(filedata)
        #    lib_settings = TSSettings(**lib_settings_data)

        return TSSettings(**settings_data)

    def to_dict(self) -> dict[str, any]:
        d = dict[str, any]()
        for prop_name, prop_value in self:
            d[prop_name] = prop_value

        return d

    def save(self, path: Path | str) -> None:
        with open(path, "w") as f:
            toml.dump(self.to_dict(), f)
