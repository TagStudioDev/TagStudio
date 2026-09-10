# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


import platform


def is_fs_case_sensitive() -> bool:
    """Whether the filesystem is case sensitive.

    NOTE: Not authoritative for OSes other than Windows.
    """
    # TODO: Make this more robust instead of assuming Windows == NTFS/exFAT
    # and other OS filesystems are automatically case sensitive.
    return platform.system() != "Windows"
