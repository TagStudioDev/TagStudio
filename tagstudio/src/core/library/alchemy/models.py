from pathlib import Path
from typing import Optional, Self

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base
from .enums import TagColor
from .fields import DatetimeField, Field, TagBoxField, TagBoxTypes, TextField


class TagAlias(Base):
    __tablename__ = "tag_aliases"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str]

    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"))
    tag: Mapped["Tag"] = relationship(back_populates="aliases")

    def __init__(self, name: str, tag: Optional["Tag"] = None):
        self.name = name

        if tag:
            self.tag = tag

        super().__init__()


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(unique=True)
    shorthand: Mapped[str | None]
    color: Mapped[TagColor]
    icon: Mapped[str | None]

    aliases: Mapped[set[TagAlias]] = relationship(back_populates="tag")

    parent_tags: Mapped[set["Tag"]] = relationship(
        secondary="tag_subtags",
        primaryjoin="Tag.id == tag_subtags.c.subtag_id",
        secondaryjoin="Tag.id == tag_subtags.c.parent_tag_id",
        back_populates="subtags",
    )

    subtags: Mapped[set["Tag"]] = relationship(
        secondary="tag_subtags",
        primaryjoin="Tag.id == tag_subtags.c.parent_tag_id",
        secondaryjoin="Tag.id == tag_subtags.c.subtag_id",
        back_populates="parent_tags",
    )

    @property
    def subtag_ids(self) -> list[int]:
        return [tag.id for tag in self.subtags]

    @property
    def alias_strings(self) -> list[str]:
        return [alias.name for alias in self.aliases]

    def __init__(
        self,
        name: str,
        shorthand: str | None = None,
        aliases: set[TagAlias] = None,
        parent_tags: set["Tag"] = None,
        subtags: set["Tag"] = None,
        icon: str | None = None,
        color: TagColor = TagColor.default,
    ):
        self.name = name
        self.aliases = aliases or set()
        self.parent_tags = parent_tags or set()
        self.subtags = subtags or set()
        self.color = color
        self.icon = icon
        self.shorthand = shorthand
        super().__init__()

    def __str__(self) -> str:
        return f"<Tag ID: {self.id} Name: {self.name}>"

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def display_name(self) -> str:
        """Returns a formatted tag name intended for displaying."""
        if self.subtags:
            first_subtag = list(self.subtags.copy())[0]
            first_subtag_display_name = first_subtag.shorthand or first_subtag.name
            return f"{self.name}" f" ({first_subtag_display_name})"
        else:
            return f"{self.name}"

    def add_subtag(self, tag: int):
        # TODO
        return
        if tag not in self.subtags:
            self.subtags.add(tag)

    def remove_subtag(self, tag: int):
        # TODO
        return
        if tag in self.subtags:
            self.subtags.remove(tag)


class Entry(Base):
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(primary_key=True)

    path: Mapped[Path] = mapped_column(unique=True)

    text_fields: Mapped[list[TextField]] = relationship(
        back_populates="entry",
        cascade="all, delete",
    )
    datetime_fields: Mapped[list[DatetimeField]] = relationship(
        back_populates="entry",
        cascade="all, delete",
    )
    tag_box_fields: Mapped[list[TagBoxField]] = relationship(
        back_populates="entry",
        cascade="all, delete",
    )

    @property
    def fields(self) -> list[Field]:
        fields: list[Field] = []
        fields.extend(self.tag_box_fields)
        fields.extend(self.text_fields)
        fields.extend(self.datetime_fields)
        fields = sorted(fields, key=lambda field: field.id)
        return fields

    @property
    def tags(self) -> set[Tag]:
        tag_set: set[Tag] = set()
        for tag_box_field in self.tag_box_fields:
            tag_set.update(tag_box_field.tags)
        return tag_set

    @property
    def favorited(self) -> bool:
        for tag_box_field in self.tag_box_fields:
            for tag in tag_box_field.tags:
                if tag.name == "Favorite":
                    return True
        return False

    @property
    def archived(self) -> bool:
        for tag_box_field in self.tag_box_fields:
            for tag in tag_box_field.tags:
                if tag.name == "Archived":
                    return True
        return False

    def __init__(
        self,
        path: Path,
        fields: list[Field] = None,
    ) -> None:
        self.path = path
        self.type = None
        self.tag_box_fields.append(
            TagBoxField(
                name="Meta Tags",
                type=TagBoxTypes.meta_tag_box,
            )
        )

        for field in fields or []:
            if isinstance(field, TextField):
                self.text_fields.append(field)
            elif isinstance(field, DatetimeField):
                self.datetime_fields.append(field)
            elif isinstance(field, TagBoxField):
                self.tag_box_fields.append(field)
            else:
                raise ValueError(f"Invalid field type: {field}")

    def has_tag(self, tag: Tag) -> bool:
        return tag in self.tags

    def remove_tag(self, tag: Tag, field: TagBoxField | None = None) -> None:
        """
        Removes a Tag from the Entry. If given a field index, the given Tag will
        only be removed from that index. If left blank, all instances of that
        Tag will be removed from the Entry.
        """
        if field:
            field.tags.remove(tag)
            return

        for tag_box_field in self.tag_box_fields:
            tag_box_field.tags.remove(tag)

    def add_tag(self, tag_id: int) -> None:
        """
        Adds a Tag to the Entry. If given a field index, the given Tag will
        only be added to that index. If left blank, the Tag will be added to
        all TagBoxFields in the Entry.
        """
        # TODO
