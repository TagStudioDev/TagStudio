# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


def escape_text(text: str):
    """Escapes characters that are problematic in Qt widgets."""
    return text.replace("&", "&&")
