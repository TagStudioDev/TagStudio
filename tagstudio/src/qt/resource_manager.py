# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import logging
from pathlib import Path
from typing import Any

import ujson

logging.basicConfig(format="%(message)s", level=logging.INFO)


class ResourceManager:
    """A resource manager for retrieving resources."""

    _map: dict[str, tuple[str, str]] = {}  # dict[<id>, tuple[<filepath>,<mode>]]
    _cache: dict[str, Any] = {}

    # Initialize _map
    with open(
        Path(__file__).parent / "resources.json", mode="r", encoding="utf-8"
    ) as f:
        json_map: dict = ujson.load(f)
        for item in json_map.items():
            _map[item[0]] = (item[1]["path"], item[1]["mode"])

    logging.info(f"[ResourceManager] Resources Loaded: {_map}")

    def __init__(self) -> None:
        pass

    def get(self, id: str) -> Any:
        """Get a resource from the ResourceManager.
        This can include resources inside and outside of QResources, and will return
        theme-respecting variations of resources if available.

        Args:
            id (str): The name of the resource.

        Returns:
            Any: The resource if found, else None.
        """
        cached_res = ResourceManager._cache.get(id, None)
        if cached_res:
            return cached_res
        else:
            path, mode = ResourceManager._map.get(id, None)
            if mode in ["r", "rb"]:
                with open((Path(__file__).parents[2] / "resources" / path), mode) as f:
                    data = f.read()

                    if mode == ["rb"]:
                        data = bytes(data)

                    ResourceManager._cache[id] = data
                    return data
            elif mode in ["qt"]:
                # TODO: Qt resource loading logic
                pass

    def __getattr__(self, __name: str) -> Any:
        attr = self.get(__name)
        if attr:
            return attr
        raise AttributeError(f"Attribute {id} not found")
