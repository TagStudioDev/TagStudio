from datetime import datetime
from pathlib import Path

import structlog
import toml
from appdirs import user_cache_dir
from pydantic import BaseModel, ConfigDict, Field

logger = structlog.get_logger(__name__)

cache_dir = Path(user_cache_dir()) / ".TagStudio"
cache_location = cache_dir / "cache.toml"


class TSCachedData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    last_library: str | None = Field(default=None)
    library_history: dict[datetime, str] = Field(default_factory=dict[datetime, str])

    path: str = Field()

    @staticmethod
    def open(path: str | None = None) -> "TSCachedData":
        file: str | None = None

        if path is None:
            if not Path(cache_dir).exists():
                logger.info("Cache directory does not exist - creating", path=cache_dir)
                Path.mkdir(cache_dir)
            if not Path(cache_location).exists():
                logger.info("Cache file does not exist - creating", path=cache_location)
                open(cache_location, "w").close()
            file = str(cache_location)
        else:
            file = path

        data = toml.load(file)
        data["path"] = str(path) if path is not None else str(cache_location)
        cached_data = TSCachedData(**data)
        return cached_data

    def save(self):
        with open(self.path, "w") as f:
            toml.dump(dict(self), f)
