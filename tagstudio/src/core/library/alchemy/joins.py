# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class TagParent(Base):
    __tablename__ = "tag_parents"

    parent_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), primary_key=True)


class TagEntry(Base):
    __tablename__ = "tag_entries"

    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), primary_key=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("entries.id"), primary_key=True)
