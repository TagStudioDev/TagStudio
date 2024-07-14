from __future__ import annotations

import datetime
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Union, Type, TypeVar, Any

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

if TYPE_CHECKING:
    from .models import Entry, Tag

Field = Union["TextField", "TagBoxField", "DatetimeField"]
FieldType = Union["TextFieldTypes", "TagBoxTypes", "DateTimeTypes"]


class TextFieldTypes(Enum):
    text_line = "Text Line"
    text_box = "Text Box"


class TagBoxTypes(Enum):
    meta_tag_box = "Meta Tags"
    tag_box = "Tags"


class DateTimeTypes(Enum):
    datetime = "Datetime"


class TextField(Base):
    __tablename__ = "text_fields"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[TextFieldTypes]

    entry_id: Mapped[int] = mapped_column(ForeignKey("entries.id"))
    entry: Mapped["Entry"] = relationship()

    value: Mapped[str | None]
    name: Mapped[str]

    def __init__(
        self,
        name: str,
        type,
        value: str | None = None,
        entry: Entry | None = None,
        entry_id: int | None = None,
    ):
        self.name = name
        self.type = type
        self.value = value
        self.entry_id = entry_id

        if entry:
            self.entry = entry
        super().__init__()

    def __key(self):
        return (self.type, self.name, self.value)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, value: object) -> bool:
        if isinstance(value, TextField):
            return self.__key() == value.__key()
        elif isinstance(value, TagBoxField):
            return False
        elif isinstance(value, DatetimeField):
            return False
        raise NotImplementedError


class TagBoxField(Base):
    __tablename__ = "tag_box_fields"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[TagBoxTypes] = mapped_column(default=TagBoxTypes.tag_box)

    entry_id: Mapped[int] = mapped_column(ForeignKey("entries.id"))
    entry: Mapped[Entry] = relationship(foreign_keys=[entry_id])

    tags: Mapped[set[Tag]] = relationship(secondary="tag_fields")
    name: Mapped[str]

    @property
    def tag_ids(self) -> list[int]:
        return [tag.id for tag in self.tags]

    def __init__(
        self,
        name: str,
        tags: set[Tag] | None = None,
        entry: Entry | None = None,
        entry_id=entry_id,
        type=TagBoxTypes.tag_box,
    ):
        self.name = name
        self.tags = tags or set()
        self.type = type
        self.entry_id = entry_id

        if entry:
            self.entry = entry
        super().__init__()

    def __key(self):
        return (self.type, self.name, str(self.tag_ids))

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, value: object) -> bool:
        if isinstance(value, TagBoxField):
            return self.__key() == value.__key()
        raise NotImplementedError


class DatetimeField(Base):
    __tablename__ = "datetime_fields"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[DateTimeTypes]

    entry_id: Mapped[int] = mapped_column(ForeignKey("entries.id"))
    entry: Mapped[Entry] = relationship()

    value: Mapped[datetime.datetime | None]
    name: Mapped[str]

    def __init__(
        self,
        name: str,
        value: datetime.datetime | None = None,
        entry: Entry | None = None,
        entry_id: int | None = None,
        type=DateTimeTypes.datetime,
    ):
        self.name = name
        self.type = type
        self.value = value

        self.entry_id = entry_id

        if entry:
            self.entry = entry
        super().__init__()

    def __key(self):
        return (self.type, self.name, self.value)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, value: object) -> bool:
        if isinstance(value, DatetimeField):
            return self.__key() == value.__key()
        raise NotImplementedError


@dataclass
class DefaultField:
    name: str
    class_: Any
    type: TextFieldTypes | TagBoxTypes | DateTimeTypes


DEFAULT_FIELDS: list[DefaultField] = [
    DefaultField(name="Title", class_=TextField, type=TextFieldTypes.text_line),
    DefaultField(name="Author", class_=TextField, type=TextFieldTypes.text_line),
    DefaultField(name="Artist", class_=TextField, type=TextFieldTypes.text_line),
    DefaultField(name="Guest Artist", class_=TextField, type=TextFieldTypes.text_line),
    DefaultField(name="Composer", class_=TextField, type=TextFieldTypes.text_line),
    DefaultField(name="URL", class_=TextField, type=TextFieldTypes.text_line),
    DefaultField(name="Source", class_=TextField, type=TextFieldTypes.text_line),
    DefaultField(name="Publisher", class_=TextField, type=TextFieldTypes.text_line),
    DefaultField(name="Description", class_=TextField, type=TextFieldTypes.text_box),
    DefaultField(name="Notes", class_=TextField, type=TextFieldTypes.text_box),
    DefaultField(name="Comments", class_=TextField, type=TextFieldTypes.text_box),
    DefaultField(name="Tags", class_=TagBoxField, type=TagBoxTypes.tag_box),
    DefaultField(name="Content Tags", class_=TagBoxField, type=TagBoxTypes.tag_box),
    DefaultField(name="Meta Tags", class_=TagBoxField, type=TagBoxTypes.tag_box),
    DefaultField(name="Date", class_=DatetimeField, type=DateTimeTypes.datetime),
    DefaultField(
        name="Date Created", class_=DatetimeField, type=DateTimeTypes.datetime
    ),
    DefaultField(
        name="Date Modified", class_=DatetimeField, type=DateTimeTypes.datetime
    ),
    DefaultField(name="Date Taken", class_=DatetimeField, type=DateTimeTypes.datetime),
    DefaultField(
        name="Date Published", class_=DatetimeField, type=DateTimeTypes.datetime
    ),
    DefaultField(
        name="Date Uploaded", class_=DatetimeField, type=DateTimeTypes.datetime
    ),
    DefaultField(
        name="Date Released", class_=DatetimeField, type=DateTimeTypes.datetime
    ),
]
