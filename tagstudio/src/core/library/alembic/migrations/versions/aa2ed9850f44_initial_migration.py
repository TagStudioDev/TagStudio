"""initial migration

Revision ID: aa2ed9850f44
Revises:
Create Date: 2024-10-26 21:27:15.801265

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import src.core.library.alchemy.db


# revision identifiers, used by Alembic.
revision: str = "aa2ed9850f44"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "folders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("path", src.core.library.alchemy.db.PathType(), nullable=False),
        sa.Column("uuid", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("path"),
        sa.UniqueConstraint("uuid"),
    )
    op.create_table(
        "preferences",
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("shorthand", sa.String(), nullable=True),
        sa.Column(
            "color",
            sa.Enum(
                "DEFAULT",
                "BLACK",
                "DARK_GRAY",
                "GRAY",
                "LIGHT_GRAY",
                "WHITE",
                "LIGHT_PINK",
                "PINK",
                "RED",
                "RED_ORANGE",
                "ORANGE",
                "YELLOW_ORANGE",
                "YELLOW",
                "LIME",
                "LIGHT_GREEN",
                "MINT",
                "GREEN",
                "TEAL",
                "CYAN",
                "LIGHT_BLUE",
                "BLUE",
                "BLUE_VIOLET",
                "VIOLET",
                "PURPLE",
                "LAVENDER",
                "BERRY",
                "MAGENTA",
                "SALMON",
                "AUBURN",
                "DARK_BROWN",
                "BROWN",
                "LIGHT_BROWN",
                "BLONDE",
                "PEACH",
                "WARM_GRAY",
                "COOL_GRAY",
                "OLIVE",
                name="tagcolor",
            ),
            nullable=False,
        ),
        sa.Column("icon", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sqlite_autoincrement=True,
    )
    op.create_table(
        "value_type",
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "type",
            sa.Enum("TEXT_LINE", "TEXT_BOX", "TAGS", "DATETIME", "BOOLEAN", name="fieldtypeenum"),
            nullable=False,
        ),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )
    op.create_table(
        "entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("folder_id", sa.Integer(), nullable=False),
        sa.Column("path", src.core.library.alchemy.db.PathType(), nullable=False),
        sa.Column("suffix", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["folder_id"],
            ["folders.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("path"),
    )
    op.create_table(
        "tag_aliases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            ["tags.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tag_subtags",
        sa.Column("parent_id", sa.Integer(), nullable=False),
        sa.Column("child_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["child_id"],
            ["tags.id"],
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["tags.id"],
        ),
        sa.PrimaryKeyConstraint("parent_id", "child_id"),
    )
    op.create_table(
        "boolean_fields",
        sa.Column("value", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("type_key", sa.String(), nullable=False),
        sa.Column("entry_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["entry_id"],
            ["entries.id"],
        ),
        sa.ForeignKeyConstraint(
            ["type_key"],
            ["value_type.key"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "datetime_fields",
        sa.Column("value", sa.String(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("type_key", sa.String(), nullable=False),
        sa.Column("entry_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["entry_id"],
            ["entries.id"],
        ),
        sa.ForeignKeyConstraint(
            ["type_key"],
            ["value_type.key"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tag_box_fields",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("type_key", sa.String(), nullable=False),
        sa.Column("entry_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["entry_id"],
            ["entries.id"],
        ),
        sa.ForeignKeyConstraint(
            ["type_key"],
            ["value_type.key"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "text_fields",
        sa.Column("value", sa.String(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("type_key", sa.String(), nullable=False),
        sa.Column("entry_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["entry_id"],
            ["entries.id"],
        ),
        sa.ForeignKeyConstraint(
            ["type_key"],
            ["value_type.key"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tag_fields",
        sa.Column("field_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["field_id"],
            ["tag_box_fields.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            ["tags.id"],
        ),
        sa.PrimaryKeyConstraint("field_id", "tag_id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("tag_fields")
    op.drop_table("text_fields")
    op.drop_table("tag_box_fields")
    op.drop_table("datetime_fields")
    op.drop_table("boolean_fields")
    op.drop_table("tag_subtags")
    op.drop_table("tag_aliases")
    op.drop_table("entries")
    op.drop_table("value_type")
    op.drop_table("tags")
    op.drop_table("preferences")
    op.drop_table("folders")
    # ### end Alembic commands ###
