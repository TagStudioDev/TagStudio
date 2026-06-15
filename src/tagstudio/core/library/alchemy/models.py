# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from datetime import datetime as dt
from pathlib import Path
from typing import override

from sqlalchemy import ForeignKey, ForeignKeyConstraint, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tagstudio.core.constants import TAG_ARCHIVED, TAG_FAVORITE
from tagstudio.core.library.alchemy.db import Base, PathType
from tagstudio.core.library.alchemy.fields import (
    BaseField,
    DatetimeField,
    TextField,
)
from tagstudio.core.library.alchemy.joins import TagParent
from tagstudio.core.library.alchemy.metadata import FileMetadata
from tagstudio.core.utils.stat import get_date_created, get_date_modified


class Namespace(Base):
    __tablename__ = "namespaces"

    namespace: Mapped[str] = mapped_column(primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)

    def __init__(
        self,
        namespace: str,
        name: str,
    ):
        self.namespace = namespace
        self.name = name
        super().__init__()


class TagAlias(Base):
    __tablename__ = "tag_aliases"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"))
    tag: Mapped["Tag"] = relationship(back_populates="aliases")

    def __init__(self, name: str, tag_id: int | None = None):
        self.name = name

        if tag_id is not None:
            self.tag_id = tag_id

        super().__init__()


class TagColorGroup(Base):
    __tablename__ = "tag_colors"

    slug: Mapped[str] = mapped_column(primary_key=True, nullable=False)
    namespace: Mapped[str] = mapped_column(
        ForeignKey("namespaces.namespace"), primary_key=True, nullable=False
    )
    name: Mapped[str] = mapped_column()
    primary: Mapped[str] = mapped_column(nullable=False)
    secondary: Mapped[str | None]
    color_border: Mapped[bool] = mapped_column(nullable=False, default=False)

    # TODO: Determine if slug and namespace can be optional and generated/added here if needed.
    def __init__(
        self,
        slug: str,
        namespace: str,
        name: str,
        primary: str,
        secondary: str | None = None,
        color_border: bool = False,
    ):
        self.slug = slug
        self.namespace = namespace
        self.name = name
        self.primary = primary
        if secondary:
            self.secondary = secondary
        self.color_border = color_border
        super().__init__()


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str]
    shorthand: Mapped[str | None]
    color_namespace: Mapped[str | None] = mapped_column()
    color_slug: Mapped[str | None] = mapped_column()
    color: Mapped[TagColorGroup | None] = relationship(lazy="joined")
    is_category: Mapped[bool]
    is_hidden: Mapped[bool]
    icon: Mapped[str | None]
    aliases: Mapped[set[TagAlias]] = relationship(back_populates="tag")
    parent_tags: Mapped[set["Tag"]] = relationship(
        secondary=TagParent.__tablename__,
        primaryjoin="Tag.id == TagParent.child_id",
        secondaryjoin="Tag.id == TagParent.parent_id",
        back_populates="parent_tags",
    )
    disambiguation_id: Mapped[int | None]

    __table_args__ = (
        ForeignKeyConstraint(
            [color_namespace, color_slug], [TagColorGroup.namespace, TagColorGroup.slug]
        ),
        {"sqlite_autoincrement": True},
    )

    @property
    def parent_ids(self) -> list[int]:
        return [tag.id for tag in self.parent_tags]

    @property
    def alias_strings(self) -> list[str]:
        return [alias.name for alias in self.aliases]

    @property
    def alias_ids(self) -> list[int]:
        return [tag.id for tag in self.aliases]

    def __init__(
        self,
        name: str,
        id: int | None = None,
        shorthand: str | None = None,
        aliases: set[TagAlias] | None = None,
        parent_tags: set["Tag"] | None = None,
        icon: str | None = None,
        color_namespace: str | None = None,
        color_slug: str | None = None,
        disambiguation_id: int | None = None,
        is_category: bool = False,
        is_hidden: bool = False,
    ):
        self.name = name
        self.aliases = aliases or set()
        self.parent_tags = parent_tags or set()
        self.color_namespace = color_namespace
        self.color_slug = color_slug
        self.icon = icon
        self.shorthand = shorthand
        self.disambiguation_id = disambiguation_id
        self.is_category = is_category
        self.is_hidden = is_hidden
        self.id = id  # pyright: ignore[reportAttributeAccessIssue]
        super().__init__()

    @override
    def __str__(self) -> str:
        return f"<Tag ID: {self.id} Name: {self.name}>"

    @override
    def __repr__(self) -> str:
        return self.__str__()

    @override
    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Tag):
            return False
        return self.id == value.id

    def __lt__(self, other: "Tag") -> bool:
        return self.name < other.name

    def __le__(self, other: "Tag") -> bool:
        return self.name <= other.name

    def __gt__(self, other: "Tag") -> bool:
        return self.name > other.name

    def __ge__(self, other: "Tag") -> bool:
        return self.name >= other.name


# TODO: Use or replace these with an actual multi-root implementation
class Folder(Base):
    __tablename__ = "folders"

    # TODO - implement this
    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[Path] = mapped_column(PathType, unique=True)
    uuid: Mapped[str] = mapped_column(unique=True)


class Entry(Base):
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(primary_key=True)

    # TODO: Use or replace these with an actual multi-root implementation
    folder_id: Mapped[int] = mapped_column(ForeignKey("folders.id"))
    folder: Mapped[Folder] = relationship("Folder")

    # TODO: Possibly move to FileMetadata table if Entry is split into Entry/FileEntry (see #588)
    path: Mapped[Path] = mapped_column(PathType, unique=True)
    filename: Mapped[str] = mapped_column()
    suffix: Mapped[str] = mapped_column()

    date_added: Mapped[dt | None]  # The date this entry was added to the library

    tags: Mapped[set[Tag]] = relationship(secondary="tag_entries")

    text_fields: Mapped[list[TextField]] = relationship(
        back_populates="entry",
        cascade="all, delete",
    )
    datetime_fields: Mapped[list[DatetimeField]] = relationship(
        back_populates="entry",
        cascade="all, delete",
    )

    file_metadata: Mapped["FileMetadata"] = relationship(
        uselist=False,
        cascade="all, delete-orphan",
    )

    @property
    def fields(self) -> list[BaseField]:
        fields: list[BaseField] = []
        fields.extend(self.text_fields)
        fields.extend(self.datetime_fields)
        return fields

    @property
    def is_favorite(self) -> bool:
        return any(tag.id == TAG_FAVORITE for tag in self.tags)

    @property
    def is_archived(self) -> bool:
        return any(tag.id == TAG_ARCHIVED for tag in self.tags)

    @property
    def date_created(self) -> float | None:
        return self.file_metadata.date_created if self.file_metadata else None

    @property
    def date_modified(self) -> float | None:
        return self.file_metadata.date_modified if self.file_metadata else None

    def __init__(
        self,
        path: Path,
        folder: Folder,
        fields: list[BaseField],
        id: int | None = None,
        date_added: dt | None = None,
        # date_created: float | None = None,
        # date_modified: float | None = None,
        path_for_file_metadata: Path | None = None,
    ) -> None:
        super().__init__()

        self.id = id  # pyright: ignore[reportAttributeAccessIssue]

        self.folder = folder  # NOTE: Currently unused
        self.path = path
        self.filename = path.name
        self.suffix = path.suffix.lstrip(".").lower()

        self.date_added = date_added  # The date this entry was added to the library

        for field in fields:
            if isinstance(field, TextField):
                self.text_fields.append(field)
            elif isinstance(field, DatetimeField):
                self.datetime_fields.append(field)
            else:
                raise ValueError(f"Invalid field type: {field}")

        if path_for_file_metadata:
            self.file_metadata = FileMetadata(
                entry_id=self.id,
                date_created=get_date_created(path_for_file_metadata),
                date_modified=get_date_modified(path_for_file_metadata),
            )

    def has_tag(self, tag: Tag) -> bool:
        return tag in self.tags

    def remove_tag(self, tag: Tag) -> None:
        """Removes a Tag from the Entry."""
        self.tags.remove(tag)


class Version(Base):
    __tablename__ = "versions"

    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[int] = mapped_column(nullable=False, default=0)
