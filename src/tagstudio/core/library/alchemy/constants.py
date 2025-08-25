from sqlalchemy import text

DB_VERSION_LEGACY_KEY: str = "DB_VERSION"
DB_VERSION_CURRENT_KEY: str = "CURRENT"
DB_VERSION_INITIAL_KEY: str = "INITIAL"
DB_VERSION: int = 101

TAG_CHILDREN_QUERY = text("""
-- Note for this entire query that tag_parents.child_id is the parent id and tag_parents.parent_id is the child id due to bad naming
WITH RECURSIVE ChildTags AS (
    SELECT :tag_id AS child_id
    UNION
    SELECT tp.parent_id AS child_id
	FROM tag_parents tp
    INNER JOIN ChildTags c ON tp.child_id = c.child_id
)
SELECT * FROM ChildTags;
""")  # noqa: E501
