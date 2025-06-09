# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import hashlib
from pathlib import Path


def _get_hash(file_path: Path) -> str:
    return hashlib.shake_128(str(file_path).encode("utf-8")).hexdigest(8)


def get_cache_path(cache_folder: Path, file_path: Path) -> Path:
    hash = _get_hash(file_path)
    folder = Path(hash[:2])
    mod_time = file_path.stat().st_mtime_ns
    return cache_folder / folder / f"{hash}-{mod_time}.webp"


def remove_from_cache(cache_folder: Path, file_path: Path):
    hash = _get_hash(file_path)
    folder = hash[:2]
    cache_folder = cache_folder / folder
    for file in cache_folder.glob("{hash}-*.webp"):
        if file.is_file():
            file.unlink(missing_ok=True)


def clear_cache(cache_folder: Path):
    for folder in cache_folder.iterdir():
        for file in folder.iterdir():
            file.unlink()
        folder.rmdir()
