# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from sqlalchemy import text

from tagstudio.core.library.alchemy.fields import (
    DatetimeFieldTemplate,
    TextFieldTemplate,
)

SQL_FILENAME: str = "ts_library.sqlite"
JSON_FILENAME: str = "ts_library.json"

DB_VERSION_CURRENT_KEY: str = "CURRENT"
DB_VERSION_INITIAL_KEY: str = "INITIAL"
DB_VERSION: int = 400

TAG_CHILDREN_QUERY = text("""
WITH RECURSIVE ChildTags AS (
    SELECT :tag_id AS tag_id
    UNION
    SELECT tp.child_id AS tag_id
    FROM tag_parents tp
    INNER JOIN ChildTags c ON tp.parent_id = c.tag_id
)
SELECT * FROM ChildTags;
""")

TAG_CHILDREN_ID_QUERY = text("""
WITH RECURSIVE ChildTags AS (
    SELECT :tag_id AS tag_id
    UNION
    SELECT tp.child_id AS tag_id
    FROM tag_parents tp
    INNER JOIN ChildTags c ON tp.parent_id = c.tag_id
)
SELECT tag_id FROM ChildTags;
""")


DEFAULT_TEXT_FIELD_TEMPLATES = (
    {"name": "Title", "is_multiline": False},
    {"name": "Author", "is_multiline": False},
    {"name": "Artist", "is_multiline": False},
    {"name": "URL", "is_multiline": False},
    {"name": "Description", "is_multiline": True},
    {"name": "Notes", "is_multiline": True},
    {"name": "Comments", "is_multiline": True},
)

DEFAULT_DATETIME_FIELD_TEMPLATES = ({"name": "Date"},)

DEFAULT_FIELD_TEMPLATES = [TextFieldTemplate(**p) for p in DEFAULT_TEXT_FIELD_TEMPLATES] + [
    DatetimeFieldTemplate(**p) for p in DEFAULT_DATETIME_FIELD_TEMPLATES
]
