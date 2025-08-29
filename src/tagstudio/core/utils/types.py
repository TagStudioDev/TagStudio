# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from typing import TypeVar

T = TypeVar("T")


def unwrap(optional: T | None, default: T | None = None) -> T:
    if optional is not None:
        return optional
    if default is not None:
        return default
    raise ValueError("Expected a value, but got None and no default was provided.")
