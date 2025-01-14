from pathlib import Path

import structlog
import toml
from pydantic import BaseModel, Field

from ..constants import DEFAULT_LIB_VERSION

logger = structlog.get_logger(__name__)


class LibSettings(BaseModel):
    is_exclude_list: bool = Field(default=True)
    extension_list: list[str] = Field(default=[".json", ".xmp", ".aae"])
    page_size: int = Field(default=500)
    db_version: int = Field(default=DEFAULT_LIB_VERSION)
    filename: str = Field(default="")

    @staticmethod
    def open(path_value: Path | str) -> "LibSettings":
        path: Path = Path(path_value) if not isinstance(path_value, Path) else path_value

        if path.exists():
            with open(path) as settings_file:
                filecontents = settings_file.read()
                if len(filecontents.strip()) != 0:
                    settings_data = toml.loads(filecontents)
                    settings_data["filename"] = str(path)
                    return LibSettings(**settings_data)

        # either settings file did not exist or was empty - either way, use default settings
        settings = LibSettings(filename=str(path))
        return settings

    def save(self):
        if self.filename == "":  # assume settings were opened for in-memory library
            return
        if not (parent_path := Path(self.filename).parent).exists():
            parent_path.mkdir()

        with open(self.filename, "w") as settings_file:
            toml.dump(dict(self), settings_file)
