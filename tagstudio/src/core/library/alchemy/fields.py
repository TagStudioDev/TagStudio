from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Union, Any, TYPE_CHECKING

from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base
from .enums import FieldTypeEnum

if TYPE_CHECKING:
    from .models import Entry, Tag, LibraryField

Field = Union["TextField", "TagBoxField", "DatetimeField"]


class BooleanField(Base):
    __tablename__ = "boolean_fields"

    id: Mapped[int] = mapped_column(primary_key=True)
    type_key: Mapped[str] = mapped_column(ForeignKey("library_fields.key"))
    type: Mapped[LibraryField] = relationship(foreign_keys=[type_key], lazy=False)

    entry_id: Mapped[int] = mapped_column(ForeignKey("entries.id"))
    entry: Mapped[Entry] = relationship()

    value: Mapped[bool]
    position: Mapped[int] = mapped_column(default=0)

    def __key(self):
        return (self.type, self.value)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, value) -> bool:
        if isinstance(value, BooleanField):
            return self.__key() == value.__key()
        raise NotImplementedError


class TextField(Base):
    __tablename__ = "text_fields"
    # constrain for combination of: entry_id, type_key and position
    __table_args__ = (
        ForeignKeyConstraint(
            ["entry_id", "type_key", "position"],
            ["text_fields.entry_id", "text_fields.type_key", "text_fields.position"],
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type_key: Mapped[str] = mapped_column(ForeignKey("library_fields.key"))
    type: Mapped[LibraryField] = relationship(foreign_keys=[type_key], lazy=False)

    entry_id: Mapped[int] = mapped_column(ForeignKey("entries.id"))
    entry: Mapped[Entry] = relationship(foreign_keys=[entry_id])

    value: Mapped[str | None]
    position: Mapped[int] = mapped_column(default=0)

    def __key(self):
        return (self.type, self.value)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, value) -> bool:
        if isinstance(value, TextField):
            return self.__key() == value.__key()
        elif isinstance(value, (TagBoxField, DatetimeField)):
            return False
        raise NotImplementedError


class TagBoxField(Base):
    __tablename__ = "tag_box_fields"

    id: Mapped[int] = mapped_column(primary_key=True)
    type_key: Mapped[str] = mapped_column(ForeignKey("library_fields.key"))
    type: Mapped[LibraryField] = relationship(foreign_keys=[type_key], lazy=False)

    entry_id: Mapped[int] = mapped_column(ForeignKey("entries.id"))
    entry: Mapped[Entry] = relationship(foreign_keys=[entry_id])

    tags: Mapped[set[Tag]] = relationship(secondary="tag_fields")
    position: Mapped[int] = mapped_column(default=0)

    def __key(self):
        return (
            self.entry_id,
            self.type_key,
        )

    @property
    def value(self) -> None:
        """For interface compatibility with other field types."""
        return None

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, value) -> bool:
        if isinstance(value, TagBoxField):
            return self.__key() == value.__key()
        raise NotImplementedError


class DatetimeField(Base):
    __tablename__ = "datetime_fields"

    id: Mapped[int] = mapped_column(primary_key=True)
    type_key: Mapped[str] = mapped_column(ForeignKey("library_fields.key"))
    type: Mapped[LibraryField] = relationship(foreign_keys=[type_key], lazy=False)

    entry_id: Mapped[int] = mapped_column(ForeignKey("entries.id"))
    entry: Mapped[Entry] = relationship(foreign_keys=[entry_id])

    value: Mapped[str | None]
    position: Mapped[int] = mapped_column(default=0)

    def __key(self):
        return (self.type, self.value)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, value) -> bool:
        if isinstance(value, DatetimeField):
            return self.__key() == value.__key()
        raise NotImplementedError


@dataclass
class DefaultField:
    id: int
    name: str
    type: Any  # TextFieldTypes | TagBoxTypes | DateTimeTypes


class _FieldID(Enum):
    """Only for bootstrapping content of DB table"""

    TITLE = DefaultField(id=0, name="Title", type=FieldTypeEnum.TEXT_LINE)
    AUTHOR = DefaultField(id=1, name="Author", type=FieldTypeEnum.TEXT_LINE)
    ARTIST = DefaultField(id=2, name="Artist", type=FieldTypeEnum.TEXT_LINE)
    URL = DefaultField(id=3, name="URL", type=FieldTypeEnum.TEXT_LINE)
    DESCRIPTION = DefaultField(id=4, name="Description", type=FieldTypeEnum.TEXT_LINE)
    NOTES = DefaultField(id=5, name="Notes", type=FieldTypeEnum.TEXT_BOX)
    TAGS = DefaultField(id=6, name="Tags", type=FieldTypeEnum.TAGS)
    TAGS_CONTENT = DefaultField(id=7, name="Content Tags", type=FieldTypeEnum.TAGS)
    TAGS_META = DefaultField(id=8, name="Meta Tags", type=FieldTypeEnum.TAGS)
    COLLATION = DefaultField(id=9, name="Collation", type=FieldTypeEnum.TEXT_LINE)
    DATE = DefaultField(id=10, name="Date", type=FieldTypeEnum.DATETIME)
    DATE_CREATED = DefaultField(id=11, name="Date Created", type=FieldTypeEnum.DATETIME)
    DATE_MODIFIED = DefaultField(
        id=12, name="Date Modified", type=FieldTypeEnum.DATETIME
    )
    DATE_TAKEN = DefaultField(id=13, name="Date Taken", type=FieldTypeEnum.DATETIME)
    DATE_PUBLISHED = DefaultField(
        id=14, name="Date Published", type=FieldTypeEnum.DATETIME
    )
    # ARCHIVED = DefaultField(id=15, name="Archived",  type=CheckboxField.checkbox)
    # FAVORITE = DefaultField(id=16, name="Favorite", type=CheckboxField.checkbox)
    BOOK = DefaultField(id=17, name="Book", type=FieldTypeEnum.TEXT_LINE)
    COMIC = DefaultField(id=18, name="Comic", type=FieldTypeEnum.TEXT_LINE)
    SERIES = DefaultField(id=19, name="Series", type=FieldTypeEnum.TEXT_LINE)
    MANGA = DefaultField(id=20, name="Manga", type=FieldTypeEnum.TEXT_LINE)
    SOURCE = DefaultField(id=21, name="Source", type=FieldTypeEnum.TEXT_LINE)
    DATE_UPLOADED = DefaultField(
        id=22, name="Date Uploaded", type=FieldTypeEnum.DATETIME
    )
    DATE_RELEASED = DefaultField(
        id=23, name="Date Released", type=FieldTypeEnum.DATETIME
    )
    VOLUME = DefaultField(id=24, name="Volume", type=FieldTypeEnum.TEXT_LINE)
    ANTHOLOGY = DefaultField(id=25, name="Anthology", type=FieldTypeEnum.TEXT_LINE)
    MAGAZINE = DefaultField(id=26, name="Magazine", type=FieldTypeEnum.TEXT_LINE)
    PUBLISHER = DefaultField(id=27, name="Publisher", type=FieldTypeEnum.TEXT_LINE)
    GUEST_ARTIST = DefaultField(
        id=28, name="Guest Artist", type=FieldTypeEnum.TEXT_LINE
    )
    COMPOSER = DefaultField(id=29, name="Composer", type=FieldTypeEnum.TEXT_LINE)
    COMMENTS = DefaultField(id=30, name="Comments", type=FieldTypeEnum.TEXT_LINE)
