# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


def clean_folder_name(folder_name: str) -> str:
    cleaned_name = folder_name
    invalid_chars = '<>:"/\\|?*.'
    for char in invalid_chars:
        cleaned_name = cleaned_name.replace(char, "_")
    return cleaned_name
