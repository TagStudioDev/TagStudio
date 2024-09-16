# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from pathlib import Path
from typing import Any

import structlog
import ujson

logger = structlog.get_logger(__name__)


class ResourceManager:
    """A resource manager for retrieving resources."""

    _map: dict = {}
    _cache: dict[str, Any] = {}
    _initialized: bool = False

    def __init__(self) -> None:
        # Load JSON resource map
        if not ResourceManager._initialized:
            with open(Path(__file__).parent / "resources.json", encoding="utf-8") as f:
                ResourceManager._map = ujson.load(f)
                logger.info("resources registered", count=len(ResourceManager._map.items()))
            ResourceManager._initialized = True

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
            if res.get("mode") in ["r", "rb"]:
                with open(
                    (Path(__file__).parents[2] / "resources" / res.get("path")),
                    res.get("mode"),
                ) as f:
                    data = f.read()
                    if res.get("mode") == "rb":
                        data = bytes(data)
                    ResourceManager._cache[id] = data
                    return data
            elif res.get("mode") in ["qt"]:
                # TODO: Qt resource loading logic
                pass

    def __getattr__(self, __name: str) -> Any:
        attr = self.get(__name)
        if attr:
            return attr
        raise AttributeError(f"Attribute {id} not found")
