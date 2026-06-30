# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pathlib import Path

import structlog
import ujson
from PIL import Image
from PySide6.QtGui import QPixmap

logger = structlog.get_logger(__name__)


RESOURCE_FOLDER: Path = Path(__file__).parents[1]


class ResourceManager:
    """A resource manager for retrieving resources."""

    _map: dict[str, dict[str, str]] = {}
    _cache: dict[str, bytes | str | Image.Image | QPixmap] = {}
    _instance: "ResourceManager | None" = None

    def __new__(cls):
        if ResourceManager._instance is None:
            ResourceManager._instance = super().__new__(cls)
            # Load JSON resource map
            with open(Path(__file__).parent / "resources.json", encoding="utf-8") as f:
                ResourceManager._map = ujson.load(f)
                logger.info(
                    "[ResourceManager] Resources Registered:",
                    count=len(ResourceManager._map.items()),
                )
        return ResourceManager._instance

    @staticmethod
    def get_path(id: str):
        """Get a resource's path from the ResourceManager.

        Args:
            id (str): The name of the resource.

        Returns:
            Path: The resource path if found, else None.
        """
        try:
            res = ResourceManager._map.get(id)
            if res is None:
                raise AttributeError
            resource_path = res.get("path")
            if resource_path is None:
                raise FileNotFoundError

        except (FileNotFoundError, AttributeError) as e:
            logger.error("[ResourceManager]: Could not find path for resource: ", id=str, error=e)
            return None

        return RESOURCE_FOLDER / "resources" / resource_path

    def get(self, id: str):
        """Get a resource from the ResourceManager.

        Args:
            id (str): The name of the resource.

        Returns:
            bytes: When the data is in byte format.
            str: When the data is in str format.
            ImageFile: When the data is in PIL.ImageFile.ImageFile format.
            QPixmap: When the data is in PySide6.QtGui.QPixmap format.
            None: If resource couldn't load.
        """
        cached_res = ResourceManager._cache.get(id)
        if cached_res is not None:
            return cached_res

        else:
            res: dict[str, str] | None = ResourceManager._map.get(id)

            try:
                if res is None:
                    raise AttributeError
                resource_path = res.get("path")
                if resource_path is None:
                    raise FileNotFoundError
            except (FileNotFoundError, AttributeError) as e:
                logger.error("[ResourceManager]: Could not find resource", id=id, error=e)
                return None

            file_path = RESOURCE_FOLDER / "resources" / resource_path
            mode = res.get("mode")

            data = None
            try:
                match mode:
                    case "r":
                        data = file_path.read_text()
                    case "rb":
                        data = file_path.read_bytes()
                    case "pil":
                        data = Image.open(file_path)
                        data.load()
                    case "qpixmap":
                        data = QPixmap(file_path.as_posix())
                    case _:
                        raise AttributeError

            except (FileNotFoundError, AttributeError) as e:
                logger.error(
                    "[ResourceManager]: Could not find resource", path=file_path, id=id, error=e
                )
                return None

        ResourceManager._cache[id] = data
        return data

    def __getattr__(self, __name: str):
        attr = self.get(__name)
        if attr is not None:
            return attr
        raise AttributeError(f"Attribute {id} not found")
