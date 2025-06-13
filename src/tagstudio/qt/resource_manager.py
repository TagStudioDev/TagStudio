# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from pathlib import Path
from typing import Literal, TypedDict

import structlog
import ujson
from PIL import Image, ImageFile
from PySide6.QtGui import QPixmap

logger = structlog.get_logger(__name__)


class TResourceJsonAttrDict(TypedDict):
    path: str
    mode: Literal["qpixmap", "pil", "rb", "r"]


TData = bytes | str | ImageFile.ImageFile | QPixmap


class ResourceManager:
    """A resource manager for retrieving resources."""

    _map: dict[str, TResourceJsonAttrDict] = {}
    _cache: dict[str, TData] = {}
    _initialized: bool = False
    _res_folder: Path = Path(__file__).parents[1]

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
        res: TResourceJsonAttrDict | None = ResourceManager._map.get(id)
        if res is not None:
            return ResourceManager._res_folder / "resources" / res.get("path")
        return None

    def get(self, id: str) -> TData | None:
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
        cached_res: TData | None = ResourceManager._cache.get(id)
        if cached_res is not None:
            return cached_res

        else:
            res: TResourceJsonAttrDict | None = ResourceManager._map.get(id)
            if res is None:
                return None

            file_path: Path = ResourceManager._res_folder / "resources" / res.get("path")
            mode = res.get("mode")

            data: TData | None = None
            try:
                if mode == "r":
                    data = file_path.read_text()

                elif mode == "rb":
                    data = file_path.read_bytes()

                elif mode == "pil":
                    data = Image.open(file_path)
                    data.load()

                elif mode == "qpixmap":
                    data = QPixmap(file_path.as_posix())

            except FileNotFoundError:
                logger.error("[ResourceManager][ERROR]: Could not find resource: ", path=file_path)

        if data is not None:
            ResourceManager._cache[id] = data
        return data

    def __getattr__(self, __name: str) -> TData:
        attr = self.get(__name)
        if attr is not None:
            return attr
        raise AttributeError(f"Attribute {id} not found")
