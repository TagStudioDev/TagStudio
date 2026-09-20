# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT

from typing import Any


class SanitizedAttr(type):
    def __getattr__(cls, name: str) -> Any:  # pyright: ignore[reportExplicitAny]
        sanitized = name.replace(".", "_")

        if sanitized == name:
            raise AttributeError(f"'{type(cls).__name__}' object has no attribute '{name}'")

        return getattr(cls, sanitized)
