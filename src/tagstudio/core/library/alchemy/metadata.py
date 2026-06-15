# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from __future__ import annotations

from datetime import datetime as dt
from pathlib import Path
from typing import TYPE_CHECKING, Any, override

from sqlalchemy import ForeignKey, ForeignKeyConstraint, Integer, null
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship


from tagstudio.core.library.alchemy.db import Base, PathType

from tagstudio.core.library.alchemy.joins import TagParent

if TYPE_CHECKING:
    from tagstudio.core.library.alchemy.models import Entry


class FileMetadata(Base):
    """Table that includes file data and metadata obtained from os.stat() for entries."""

    __tablename__ = "file_metadata"

    entry_id: Mapped[int] = mapped_column(
        ForeignKey("entries.id"), primary_key=True, nullable=False
    )

    # NOTE: These dates are stored as floats because that's their natural form from os.stat()
    # and comparisons are quicker without having to convert to/from datetime objects.
    date_created: Mapped[float | None]
    date_modified: Mapped[float | None]

    def __init__(
        self,
        entry_id: int,
        date_created: float | None = None,
        date_modified: float | None = None,
    ) -> None:
        super().__init__()
        self.entry_id = entry_id

        # # Path data
        # self.path = path
        # self.filename = path.name
        # self.suffix = path.suffix.lstrip(".").lower()

        # File metadata
        self.date_created = date_created  # st_birthtime on Windows and Mac, st_ctime on Linux
        self.date_modified = date_modified  # st_mtime


class ExifMetadata(Base):
    """Contains Exif metadata for a entries."""

    __tablename__ = "exif_metadata"

    entry_id: Mapped[int] = mapped_column(
        ForeignKey("entries.id"), primary_key=True, nullable=False
    )
    date_taken: Mapped[dt | None]

    def __init__(
        self,
        entry_id: int,
        date_taken: dt | None = None,
    ) -> None:
        super().__init__()
        self.entry_id = entry_id
        self.date_taken = date_taken  # Exif.Image.DateTime


class DimensionMetadata(Base):
    """Contains dimension metadata for entries (e.g. image and video files)."""

    __tablename__ = "dimension_metadata"

    entry_id: Mapped[int] = mapped_column(
        ForeignKey("entries.id"), primary_key=True, nullable=False
    )
    width: Mapped[int] = mapped_column(nullable=False)
    height: Mapped[int] = mapped_column(nullable=False)

    def __init__(
        self,
        entry_id: int,
        width: int,
        height: int,
    ) -> None:
        super().__init__()
        self.entry_id = entry_id
        self.width = width
        self.height = height


class DurationMetadata(Base):
    """Contains duration metadata for entries (e.g. audio and video files)."""

    __tablename__ = "duration_metadata"

    entry_id: Mapped[int] = mapped_column(
        ForeignKey("entries.id"), primary_key=True, nullable=False
    )
    duration: Mapped[float] = mapped_column(nullable=False)

    def __init__(
        self,
        entry_id: int,
        duration: float,
    ) -> None:
        super().__init__()
        self.entry_id = entry_id
        self.duration = duration
