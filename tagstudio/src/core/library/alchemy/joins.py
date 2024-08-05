from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class TagSubtag(Base):
    __tablename__ = "tag_subtags"

    parent_tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), primary_key=True)
    subtag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), primary_key=True)


class TagField(Base):
    __tablename__ = "tag_fields"

    field_id: Mapped[int] = mapped_column(
        ForeignKey("tag_box_fields.id"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), primary_key=True)
