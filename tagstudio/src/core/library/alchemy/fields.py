# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from .db import Base
from .enums import FieldTypeEnum

if TYPE_CHECKING:
    from .models import Entry, ValueType


class BaseField(Base):
    __abstract__ = True

    @declared_attr
    def id(self) -> Mapped[int]:
        return mapped_column(primary_key=True, autoincrement=True)

    @declared_attr
    def type_key(self) -> Mapped[str]:
        return mapped_column(ForeignKey("value_type.key"))

    @declared_attr
    def type(self) -> Mapped[ValueType]:
        return relationship(foreign_keys=[self.type_key], lazy=False)  # type: ignore

    @declared_attr
    def entry_id(self) -> Mapped[int]:
        return mapped_column(ForeignKey("entries.id"))

    @declared_attr
    def entry(self) -> Mapped[Entry]:
        return relationship(foreign_keys=[self.entry_id])  # type: ignore

    @declared_attr
    def position(self) -> Mapped[int]:
        return mapped_column(default=0)

    def __hash__(self):
        return hash(self.__key())

    def __key(self):
        raise NotImplementedError

    value: Any


class BooleanField(BaseField):
    __tablename__ = "boolean_fields"

    value: Mapped[bool]

    def __key(self):
        return (self.type, self.value)

    def __eq__(self, value) -> bool:
        if isinstance(value, BooleanField):
            return self.__key() == value.__key()
        raise NotImplementedError


class TextField(BaseField):
    __tablename__ = "text_fields"

    value: Mapped[str | None]

    def __key(self) -> tuple:
        return self.type, self.value

    def __eq__(self, value) -> bool:
        if isinstance(value, TextField):
            return self.__key() == value.__key()
        elif isinstance(value, DatetimeField):
            return False
        raise NotImplementedError


class DatetimeField(BaseField):
    __tablename__ = "datetime_fields"

    value: Mapped[str | None]

    def __key(self):
        return (self.type, self.value)

    def __eq__(self, value) -> bool:
        if isinstance(value, DatetimeField):
            return self.__key() == value.__key()
        raise NotImplementedError


@dataclass
class DefaultField:
    id: int
    name: str
    type: FieldTypeEnum
    is_default: bool = field(default=False)


class _FieldID(Enum):
    """Only for bootstrapping content of DB table."""

    TITLE = DefaultField(id=0, name="Title", type=FieldTypeEnum.TEXT_LINE, is_default=True)
    AUTHOR = DefaultField(id=1, name="Author", type=FieldTypeEnum.TEXT_LINE)
    ARTIST = DefaultField(id=2, name="Artist", type=FieldTypeEnum.TEXT_LINE)
    URL = DefaultField(id=3, name="URL", type=FieldTypeEnum.TEXT_LINE)
    DESCRIPTION = DefaultField(id=4, name="Description", type=FieldTypeEnum.TEXT_BOX)
    NOTES = DefaultField(id=5, name="Notes", type=FieldTypeEnum.TEXT_BOX)
    COLLATION = DefaultField(id=9, name="Collation", type=FieldTypeEnum.TEXT_LINE)
    DATE = DefaultField(id=10, name="Date", type=FieldTypeEnum.DATETIME)
    DATE_CREATED = DefaultField(id=11, name="Date Created", type=FieldTypeEnum.DATETIME)
    DATE_MODIFIED = DefaultField(id=12, name="Date Modified", type=FieldTypeEnum.DATETIME)
    DATE_TAKEN = DefaultField(id=13, name="Date Taken", type=FieldTypeEnum.DATETIME)
    DATE_PUBLISHED = DefaultField(id=14, name="Date Published", type=FieldTypeEnum.DATETIME)
    # ARCHIVED = DefaultField(id=15, name="Archived",  type=CheckboxField.checkbox)
    # FAVORITE = DefaultField(id=16, name="Favorite", type=CheckboxField.checkbox)
    BOOK = DefaultField(id=17, name="Book", type=FieldTypeEnum.TEXT_LINE)
    COMIC = DefaultField(id=18, name="Comic", type=FieldTypeEnum.TEXT_LINE)
    SERIES = DefaultField(id=19, name="Series", type=FieldTypeEnum.TEXT_LINE)
    MANGA = DefaultField(id=20, name="Manga", type=FieldTypeEnum.TEXT_LINE)
    SOURCE = DefaultField(id=21, name="Source", type=FieldTypeEnum.TEXT_LINE)
    DATE_UPLOADED = DefaultField(id=22, name="Date Uploaded", type=FieldTypeEnum.DATETIME)
    DATE_RELEASED = DefaultField(id=23, name="Date Released", type=FieldTypeEnum.DATETIME)
    VOLUME = DefaultField(id=24, name="Volume", type=FieldTypeEnum.TEXT_LINE)
    ANTHOLOGY = DefaultField(id=25, name="Anthology", type=FieldTypeEnum.TEXT_LINE)
    MAGAZINE = DefaultField(id=26, name="Magazine", type=FieldTypeEnum.TEXT_LINE)
    PUBLISHER = DefaultField(id=27, name="Publisher", type=FieldTypeEnum.TEXT_LINE)
    GUEST_ARTIST = DefaultField(id=28, name="Guest Artist", type=FieldTypeEnum.TEXT_LINE)
    COMPOSER = DefaultField(id=29, name="Composer", type=FieldTypeEnum.TEXT_LINE)
    COMMENTS = DefaultField(id=30, name="Comments", type=FieldTypeEnum.TEXT_LINE)
