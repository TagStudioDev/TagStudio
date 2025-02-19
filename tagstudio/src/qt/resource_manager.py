# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from pathlib import Path
from typing import Any

import structlog
import ujson
from PIL import (
    Image,
    ImageQt,
)
from PySide6.QtGui import QPixmap

logger = structlog.get_logger(__name__)


class ResourceManager:
    """A resource manager for retrieving resources."""

    _map: dict = {}
    _cache: dict[str, Any] = {}
    _initialized: bool = False
    _res_folder: Path = Path(__file__).parents[2]

    def __init__(self) -> None:
        # Load JSON resource map
        if not ResourceManager._initialized:
            with open(Path(__file__).parent / "resources.json", encoding="utf-8") as f:
                ResourceManager._map = ujson.load(f)
                logger.info(
                    "[ResourceManager] Resources Registered:",
                    count=len(ResourceManager._map.items()),
                )
            ResourceManager._initialized = True

    @staticmethod
    def get_path(id: str) -> Path | None:
        """Get a resource's path from the ResourceManager.

        Args:
            id (str): The name of the resource.

        Returns:
            Path: The resource path if found, else None.
        """
        res: dict = ResourceManager._map.get(id)
        if res:
            return ResourceManager._res_folder / "resources" / res.get("path")
        return None

    def get(self, id: str) -> Any:
        """Get a resource from the ResourceManager.

        This can include resources inside and outside of QResources, and will return
        theme-respecting variations of resources if available.

        Args:
            id (str): The name of the resource.

        Returns:
            Any: The resource if found, else None.
        """
        cached_res = ResourceManager._cache.get(id)
        if cached_res:
            return cached_res
        else:
            res: dict = ResourceManager._map.get(id)
            if not res:
                return None
            try:
                if res.get("mode") in ["r", "rb"]:
                    with open(
                        (ResourceManager._res_folder / "resources" / res.get("path")),
                        res.get("mode"),
                    ) as f:
                        data = f.read()
                        if res.get("mode") == "rb":
                            data = bytes(data)
                        ResourceManager._cache[id] = data
                        return data
                elif res and res.get("mode") == "pil":
                    data = Image.open(ResourceManager._res_folder / "resources" / res.get("path"))
                    return data
                elif res.get("mode") in ["qpixmap"]:
                    data = Image.open(ResourceManager._res_folder / "resources" / res.get("path"))
                    qim = ImageQt.ImageQt(data)
                    pixmap = QPixmap.fromImage(qim)
                    ResourceManager._cache[id] = pixmap
                    return pixmap
            except FileNotFoundError:
                path: Path = ResourceManager._res_folder / "resources" / res.get("path")
                logger.error("[ResourceManager][ERROR]: Could not find resource: ", path=path)
                return None

    def __getattr__(self, __name: str) -> Any:
        attr = self.get(__name)
        if attr:
            return attr
        raise AttributeError(f"Attribute {id} not found")
