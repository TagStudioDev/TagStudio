from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .field import DatetimeField, Field, TagBoxField, TagBoxTypes, TextField
from .tag import Tag


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

    # TODO
    # # Any Type
    # alts: Mapped[list[Entry]] = None

    # # Image/Video
    # self.dimensions: tuple[int, int] = None
    # self.crop: tuple[int, int, int, int] = None
    # self.mask: list[id] = None

    # # Video
    # self.length: float = None
    # self.trim: tuple[float, float] = None

    # # Text
    # self.word_count: int = None

    def __init__(
        self,
        path: Path,
        fields: list[Field] = [],
    ) -> None:
        self.path = path
        self.type = None
        self.tag_box_fields.append(
            TagBoxField(
                name="Meta Tags",
                type=TagBoxTypes.meta_tag_box,
            )
        )

        for field in fields:
            if isinstance(field, TextField):
                self.text_fields.append(field)
            elif isinstance(field, DatetimeField):
                self.datetime_fields.append(field)
            else:
                self.tag_box_fields.append(field)

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

    def add_tag(self, tag: Tag, field: TagBoxField):
        field.tags.add(tag)
