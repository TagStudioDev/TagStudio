# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import semver


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


def is_version_outdated(current: str, latest: str) -> bool:
    vcur = semver.Version.parse(current)
    vlat = semver.Version.parse(latest)
    assert vlat.prerelease is None and vlat.build is None

    if vcur.major != vlat.major:
        return vcur.major < vlat.major
    elif vcur.minor != vlat.minor:
        return vcur.minor < vlat.minor
    elif vcur.patch != vlat.patch:
        return vcur.patch < vlat.patch
    else:
        return vcur.prerelease is not None or vcur.build is not None


def format_duration(duration: int | float) -> str:
    """Format a duration in seconds as M:SS or H:MM:SS."""
    try:
        seconds = int(float(duration))
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        return f"{hours}:{minutes:02}:{seconds:02}" if hours else f"{minutes}:{seconds:02}"
    except (OverflowError, ValueError):
        return "-:--"
