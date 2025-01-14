from pathlib import Path

import structlog
import toml
from appdirs import user_cache_dir
from pydantic import BaseModel, ConfigDict, Field

logger = structlog.get_logger(__name__)

cache_dir = Path(user_cache_dir()) / "TagStudio"
cache_location = cache_dir / "cache.toml"


class TSCachedData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    last_library: str | None = Field(default=None)
    # a dict of ISO formatted date strings -> paths
    library_history: dict[str, str] = Field(default_factory=dict[str, str])

    path: str = Field()

    @staticmethod
    def open(path_value: Path | str | None = None) -> "TSCachedData":
        path: Path | None = None
        default_cache_location = Path(user_cache_dir()) / "ts_cache.toml"
        if isinstance(path_value, str):
            path = Path(path_value)
        elif isinstance(path_value, Path):
            path = path_value
        else:
            logger.info(
                "no cache location was specified, using ",
                default_cache_location=default_cache_location,
            )
            path = default_cache_location

        if path.exists():
            with open(path) as cache_file:
                filecontents = cache_file.read()
                if len(filecontents.strip()) != 0:
                    cache_data = toml.loads(filecontents)
                    cache_data["path"] = str(path)
                    logger.info("opening cache file at ", cache_location=path)
                    return TSCachedData(**cache_data)

        return TSCachedData(path=str(default_cache_location))

    def save(self):
        with open(self.path, "w") as f:
            file_data = dict(self)
            file_data.pop("path")
            toml.dump(file_data, f)
