# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


import json
from pathlib import Path
from typing import Any, Self, cast

import structlog
import toml
from pydantic import BaseModel, Field, ValidationError

from tagstudio.core.utils.types import unwrap

logger = structlog.get_logger(__name__)


class BaseDataFile(BaseModel):
    """A pydantic model loaded from and saved to a JSON or TOML file."""

    version: int = 1
    path: Path | None = Field(default=None, exclude=True)

    @classmethod
    def load(cls, path: Path) -> Self:
        """Read the model from a file, using defaults for any missing or invalid values."""
        logger.info("[BaseDataFile] Loading file...", path=path)
        data = cls._read_values(path)
        data["path"] = path
        try:
            return cls(**data)
        except ValidationError as error:
            invalid_keys = {issue["loc"][0] for issue in error.errors() if issue["loc"]}
            logger.warning("[BaseDataFile] Ignored invalid values", path=path, keys=invalid_keys)
            return cls(**{key: value for key, value in data.items() if key not in invalid_keys})

    @staticmethod
    def _read_values(path: Path) -> dict[str, Any]:
        """Read a file's values, leaving out any that can't be parsed."""
        # Check if the file exists and is readable
        try:
            if not path.exists():
                return {}
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            logger.warning("[BaseDataFile] Couldn't read file", path=path, error=error)
            return {}

        # Read a JSON file
        if path.suffix == ".json":
            try:
                data = json.loads(text)
            except ValueError:
                data = None
            if isinstance(data, dict):
                return cast(dict[str, Any], data)  # Return parsed file as an expected JSON dict

            logger.warning("[BaseDataFile] Ignored malformed file", path=path)
            return {}

        # Read a TOML file
        try:
            return toml.loads(text)
        except ValueError:
            pass
        # Parse line by line if the read failed, excluding malformed lines
        # NOTE: Parsing line by line only works for files without tables or multi-line values.
        values: dict[str, Any] = {}
        malformed_lines: list[int] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            try:
                values.update(toml.loads(line))
            except ValueError:
                malformed_lines.append(line_number)
        logger.warning("[BaseDataFile] Ignored malformed lines", path=path, lines=malformed_lines)
        return values

    def save(self) -> None:
        """Write the data file to its path."""
        path = unwrap(self.path)
        data = self.model_dump(mode="json")
        if path.suffix == ".json":
            text = json.dumps(data, indent=4, ensure_ascii=False)
        else:
            text = toml.dumps(data)

        # Write to a temp file first and then swap the original file for it.
        # Avoids partial writes on crashes or other failed writes.
        temp_path = path.with_name(f"{path.name}.tmp")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            temp_path.write_text(text, encoding="utf-8")
            temp_path.replace(path)
        except OSError as error:
            logger.warning("[BaseDataFile] Couldn't save file", path=path, error=error)
