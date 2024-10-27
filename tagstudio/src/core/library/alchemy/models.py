from pathlib import Path
from typing import Optional

from sqlalchemy import JSON, ForeignKey, Integer, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...constants import TAG_ARCHIVED, TAG_FAVORITE
from .db import Base, PathType
from .enums import TagColor
from .fields import (
    BaseField,
    BooleanField,
    DatetimeField,
    FieldTypeEnum,
    TagBoxField,
    TextField,
    _FieldID,
)
from .joins import TagSubtag


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
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(unique=True)
    shorthand: Mapped[str | None]
    color: Mapped[TagColor]
    icon: Mapped[str | None]

    aliases: Mapped[set[TagAlias]] = relationship(back_populates="tag")

    parent_tags: Mapped[set["Tag"]] = relationship(
        secondary=TagSubtag.__tablename__,
        primaryjoin="Tag.id == TagSubtag.child_id",
        secondaryjoin="Tag.id == TagSubtag.parent_id",
        back_populates="subtags",
    )

    subtags: Mapped[set["Tag"]] = relationship(
        secondary=TagSubtag.__tablename__,
        primaryjoin="Tag.id == TagSubtag.parent_id",
        secondaryjoin="Tag.id == TagSubtag.child_id",
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
        aliases: set[TagAlias] | None = None,
        parent_tags: set["Tag"] | None = None,
        subtags: set["Tag"] | None = None,
        icon: str | None = None,
        color: TagColor = TagColor.DEFAULT,
        id: int | None = None,
    ):
        self.name = name
        self.aliases = aliases or set()
        self.parent_tags = parent_tags or set()
        self.subtags = subtags or set()
        self.color = color
        self.icon = icon
        self.shorthand = shorthand
        assert not self.id
        self.id = id
        super().__init__()

    def __str__(self) -> str:
        return f"<Tag ID: {self.id} Name: {self.name}>"

    def __repr__(self) -> str:
        return self.__str__()


class Folder(Base):
    __tablename__ = "folders"

    # TODO - implement this
    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[Path] = mapped_column(PathType, unique=True)
    uuid: Mapped[str] = mapped_column(unique=True)


class Entry(Base):
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(primary_key=True)

    folder_id: Mapped[int] = mapped_column(ForeignKey("folders.id"))
    folder: Mapped[Folder] = relationship("Folder")

    path: Mapped[Path] = mapped_column(PathType, unique=True)
    suffix: Mapped[str] = mapped_column()

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
    def fields(self) -> list[BaseField]:
        fields: list[BaseField] = []
        fields.extend(self.tag_box_fields)
        fields.extend(self.text_fields)
        fields.extend(self.datetime_fields)
        fields = sorted(fields, key=lambda field: field.type.position)
        return fields

    @property
    def tags(self) -> set[Tag]:
        tag_set: set[Tag] = set()
        for tag_box_field in self.tag_box_fields:
            tag_set.update(tag_box_field.tags)
        return tag_set

    @property
    def is_favorited(self) -> bool:
        for tag_box_field in self.tag_box_fields:
            if tag_box_field.type_key == _FieldID.TAGS_META.name:
                for tag in tag_box_field.tags:
                    if tag.id == TAG_FAVORITE:
                        return True
        return False

    @property
    def is_archived(self) -> bool:
        for tag_box_field in self.tag_box_fields:
            if tag_box_field.type_key == _FieldID.TAGS_META.name:
                for tag in tag_box_field.tags:
                    if tag.id == TAG_ARCHIVED:
                        return True
        return False

    def __init__(
        self,
        path: Path,
        folder: Folder,
        fields: list[BaseField],
    ) -> None:
        self.path = path
        self.folder = folder

        self.suffix = path.suffix.lstrip(".").lower()

        for field in fields:
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
        """Removes a Tag from the Entry.

        If given a field index, the given Tag will
        only be removed from that index. If left blank, all instances of that
        Tag will be removed from the Entry.
        """
        if field:
            field.tags.remove(tag)
            return

        for tag_box_field in self.tag_box_fields:
            tag_box_field.tags.remove(tag)


class ValueType(Base):
    """Define Field Types in the Library.

    Example:
        key: content_tags (this field is slugified `name`)
        name: Content Tags (this field is human readable name)
        kind: type of content (Text Line, Text Box, Tags, Datetime, Checkbox)
        is_default: Should the field be present in new Entry?
        order: position of the field widget in the Entry form

    """

    __tablename__ = "value_type"

    key: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    type: Mapped[FieldTypeEnum] = mapped_column(default=FieldTypeEnum.TEXT_LINE)
    is_default: Mapped[bool]
    position: Mapped[int]

    # add relations to other tables
    text_fields: Mapped[list[TextField]] = relationship("TextField", back_populates="type")
    datetime_fields: Mapped[list[DatetimeField]] = relationship(
        "DatetimeField", back_populates="type"
    )
    tag_box_fields: Mapped[list[TagBoxField]] = relationship("TagBoxField", back_populates="type")
    boolean_fields: Mapped[list[BooleanField]] = relationship("BooleanField", back_populates="type")

    @property
    def as_field(self) -> BaseField:
        FieldClass = {  # noqa: N806
            FieldTypeEnum.TEXT_LINE: TextField,
            FieldTypeEnum.TEXT_BOX: TextField,
            FieldTypeEnum.TAGS: TagBoxField,
            FieldTypeEnum.DATETIME: DatetimeField,
            FieldTypeEnum.BOOLEAN: BooleanField,
        }

        return FieldClass[self.type](
            type_key=self.key,
            position=self.position,
        )


@event.listens_for(ValueType, "before_insert")
def slugify_field_key(mapper, connection, target):
    """Slugify the field key before inserting into the database."""
    if not target.key:
        from .library import slugify

        target.key = slugify(target.tag)


class Preferences(Base):
    __tablename__ = "preferences"

    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
