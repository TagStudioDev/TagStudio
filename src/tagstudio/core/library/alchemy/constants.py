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


def default_field_templates() -> tuple[TextFieldTemplate | DatetimeFieldTemplate, ...]:
    """Build a fresh set of default field template instances.

    These must be constructed anew on every call rather than shared as module-level
    singletons. SQLAlchemy instances remember their persistent identity once they've been
    added and flushed to a session; reusing the same instances across multiple `Library`
    (and therefore multiple database engines/sessions) causes every `Library` after the
    first to silently skip inserting these rows, since SQLAlchemy assumes they already
    exist.
    """
    return (
        TextFieldTemplate(name="Title"),
        TextFieldTemplate(name="Author"),
        TextFieldTemplate(name="Artist"),
        TextFieldTemplate(name="URL"),
        TextFieldTemplate(name="Description", is_multiline=True),
        TextFieldTemplate(name="Notes", is_multiline=True),
        TextFieldTemplate(name="Comments", is_multiline=True),
        DatetimeFieldTemplate(name="Date"),
    )
