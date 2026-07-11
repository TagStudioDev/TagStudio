# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from sqlalchemy import text

SQL_FILENAME: str = "ts_library.sqlite"
JSON_FILENAME: str = "ts_library.json"

DB_VERSION_CURRENT_KEY: str = "CURRENT"
DB_VERSION_INITIAL_KEY: str = "INITIAL"
DB_VERSION: int = 203

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
