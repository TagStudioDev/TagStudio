# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


class FieldTemplate:
    """A TagStudio Library Field Template object."""

    def __init__(self, id: int, name: str, type: str) -> None:
        self.id = id
        self.name = name
        self.type = type

    def __str__(self) -> str:
        return f"\nID: {self.id}\nName: {self.name}\nType: {self.type}\n"

    def __repr__(self) -> str:
        return self.__str__()

    def to_compressed_obj(self) -> dict:
        """An alternative to __dict__ that only includes fields containing non-default data."""
        obj = {}
        # All Field fields (haha) are mandatory, so no value checks are done.
        obj["id"] = self.id
        obj["name"] = self.name
        obj["type"] = self.type

        return obj
