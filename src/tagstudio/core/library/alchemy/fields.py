# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from tagstudio.core.library.alchemy.db import Base

if TYPE_CHECKING:
    from tagstudio.core.library.alchemy.models import Entry


class BaseField(Base):
    __abstract__ = True

    @declared_attr
    def id(self) -> Mapped[int]:
        return mapped_column(primary_key=True, autoincrement=True, sort_order=1)

    @declared_attr
    def name(self) -> Mapped[str]:
        return mapped_column(nullable=False, default="", sort_order=2)

    @declared_attr
    def entry_id(self) -> Mapped[int]:
        return mapped_column(ForeignKey("entries.id"), sort_order=3)

    @declared_attr
    def entry(self) -> Mapped[Entry]:
        return relationship(foreign_keys=[self.entry_id])  # type: ignore # pyright: ignore[reportArgumentType]

    @property
    def class_name(self) -> str:
        return self.__class__.__name__

    def clone_with_entry_id(self, entry_id: int) -> BaseField:  # pyright: ignore
        raise NotImplementedError()

    value: Any  # pyright: ignore


class TextField(BaseField):
    __tablename__ = "text_fields"

    value: Mapped[str | None] = mapped_column(sort_order=4)
    is_multiline: Mapped[bool] = mapped_column(nullable=False, default=False)

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TextField):
            return False

        return (self.name, self.value, self.is_multiline) == (
            other.name,
            other.value,
            other.is_multiline,
        )

    @override
    def __hash__(self) -> int:
        return hash((self.name, self.value, self.is_multiline))

    @override
    def clone_with_entry_id(self, entry_id: int) -> TextField:
        return TextField(
            name=self.name, entry_id=entry_id, value=self.value, is_multiline=self.is_multiline
        )


class DatetimeField(BaseField):
    __tablename__ = "datetime_fields"

    value: Mapped[str | None] = mapped_column(sort_order=4)

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DatetimeField):
            return False

        return (self.name, self.value) == (other.name, other.value)

    @override
    def __hash__(self) -> int:
        return hash((self.name, self.value))

    @override
    def clone_with_entry_id(self, entry_id: int) -> DatetimeField:
        return DatetimeField(name=self.name, entry_id=entry_id, value=self.value)


class BaseFieldTemplate(Base):
    __abstract__ = True

    @declared_attr
    def id(self) -> Mapped[int]:
        return mapped_column(primary_key=True, autoincrement=True)

    @declared_attr
    def name(self) -> Mapped[str]:
        return mapped_column(nullable=False, default="")

    @property
    def class_name(self) -> str:
        return self.__class__.__name__

    def to_field(self, value: Any | None = None) -> BaseField:  # pyright: ignore
        raise NotImplementedError()


class TextFieldTemplate(BaseFieldTemplate):
    __tablename__ = "text_field_templates"
    is_multiline: Mapped[bool] = mapped_column(nullable=False, default=False)

    @override
    def to_field(self, value: str | None = None) -> TextField:
        return TextField(name=self.name, value=value, is_multiline=self.is_multiline)


class DatetimeFieldTemplate(BaseFieldTemplate):
    __tablename__ = "datetime_field_templates"

    @override
    def to_field(self, value: str | None = None) -> DatetimeField:
        return DatetimeField(name=self.name, value=value)


# Used for migrating legacy libraries.
# Legacy JSON libraries (<v9.4) use an integer ID.
# SQLite libraries 6 until 200 use a slugfield name (e.g. "DATE_CREATED").
LEGACY_FIELD_MAP = {
    0: {"type": TextField, "name": "Title", "is_multiline": False},
    1: {"type": TextField, "name": "Author", "is_multiline": False},
    2: {"type": TextField, "name": "Artist", "is_multiline": False},
    3: {"type": TextField, "name": "URL", "is_multiline": False},
    4: {"type": TextField, "name": "Description", "is_multiline": True},
    5: {"type": TextField, "name": "Notes", "is_multiline": True},
    9: {"type": TextField, "name": "Collation", "is_multiline": False},
    10: {"type": DatetimeField, "name": "Date", "is_multiline": False},
    11: {"type": DatetimeField, "name": "Date Created"},
    12: {"type": DatetimeField, "name": "Date Modified"},
    13: {"type": DatetimeField, "name": "Date Taken"},
    14: {"type": DatetimeField, "name": "Date Published"},
    17: {"type": TextField, "name": "Book", "is_multiline": False},
    18: {"type": TextField, "name": "Comic", "is_multiline": False},
    19: {"type": TextField, "name": "Series", "is_multiline": False},
    20: {"type": TextField, "name": "Manga", "is_multiline": False},
    21: {"type": TextField, "name": "Source", "is_multiline": False},
    22: {"type": DatetimeField, "name": "Date Uploaded"},
    23: {"type": DatetimeField, "name": "Date Released"},
    24: {"type": TextField, "name": "Volume", "is_multiline": False},
    25: {"type": TextField, "name": "Anthology", "is_multiline": False},
    26: {"type": TextField, "name": "Magazine", "is_multiline": False},
    27: {"type": TextField, "name": "Publisher", "is_multiline": False},
    28: {"type": TextField, "name": "Guest Artist", "is_multiline": False},
    29: {"type": TextField, "name": "Composer", "is_multiline": False},
    30: {"type": TextField, "name": "Comments", "is_multiline": True},
}
