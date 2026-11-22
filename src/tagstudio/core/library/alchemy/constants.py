# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from tagstudio.core.library.alchemy.fields import (
    DatetimeFieldTemplate,
    TextFieldTemplate,
)

SQL_FILENAME: str = "ts_library.sqlite"
JSON_FILENAME: str = "ts_library.json"

DB_VERSION_CURRENT_KEY: str = "CURRENT"
DB_VERSION_INITIAL_KEY: str = "INITIAL"
DB_VERSION: int = 502

# Interval for how often a search query will check for a cancel signal
# NOTE: This gets used in the tests via monkey patching
CANCEL_SEARCH_INTERVAL: int = 100_000


DEFAULT_FIELD_TEMPLATES = (
    TextFieldTemplate(name="Title"),
    TextFieldTemplate(name="Author"),
    TextFieldTemplate(name="Artist"),
    TextFieldTemplate(name="URL"),
    TextFieldTemplate(name="Description", is_multiline=True),
    TextFieldTemplate(name="Notes", is_multiline=True),
    TextFieldTemplate(name="Comments", is_multiline=True),
    DatetimeFieldTemplate(name="Date"),
)
