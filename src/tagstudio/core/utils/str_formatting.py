# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import re

from tagstudio.core.utils.types import unwrap


def strip_punctuation(string: str) -> str:
    """Returns a given string stripped of all punctuation characters."""
    return (
        string.replace("(", "")
        .replace(")", "")
        .replace("[", "")
        .replace("]", "")
        .replace("{", "")
        .replace("}", "")
        .replace("'", "")
        .replace("`", "")
        .replace("’", "")
        .replace("‘", "")
        .replace('"', "")
        .replace("“", "")
        .replace("”", "")
        .replace("_", "")
        .replace("-", "")
        .replace(" ", "")
        .replace("　", "")
    )


def strip_web_protocol(string: str) -> str:
    r"""Strips a leading web protocol (ex. \"https://\") as well as \"www.\" from a string."""
    prefixes = ["https://", "http://", "www.", "www2."]
    for prefix in prefixes:
        string = string.removeprefix(prefix)
    return string


def is_version_outdated(current, latest) -> bool:
    regex = re.compile(r"^(\d+)\.(\d+)\.(\d+)(-\w+)?$")
    mcurrent = unwrap(regex.match(current))
    mlatest = unwrap(regex.match(latest))

    return (
        int(mlatest[1]) > int(mcurrent[1])
        or (mlatest[1] == mcurrent[1] and int(mlatest[2]) > int(mcurrent[2]))
        or (
            mlatest[1] == mcurrent[1]
            and mlatest[2] == mcurrent[2]
            and int(mlatest[3]) > int(mcurrent[3])
        )
        or (
            mlatest[1] == mcurrent[1]
            and mlatest[2] == mcurrent[2]
            and mlatest[3] == mcurrent[3]
            and (mlatest[4] is None and mcurrent[4] is not None)
        )
    )
