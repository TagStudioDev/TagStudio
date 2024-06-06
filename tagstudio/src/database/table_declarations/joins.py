from sqlalchemy import Column, ForeignKey, Integer, Table

from .base import Base

tag_subtags = Table(
    "tag_subtags",
    Base.metadata,
    Column("parent_tag_id", Integer, ForeignKey("tags.id")),
    Column("subtag_id", Integer, ForeignKey("tags.id")),
)

tag_fields = Table(
    "tag_fields",
    Base.metadata,
    Column("field_id", Integer, ForeignKey("tag_box_fields.id")),
    Column("tag_id", Integer, ForeignKey("tags.id")),
)
