# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


def unwrap[T](optional: T | None, default: T | None = None) -> T:
    if optional is not None:
        return optional
    if default is not None:
        return default
    raise ValueError("Expected a value, but got None and no default was provided.")
