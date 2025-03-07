# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

from pathlib import Path

import structlog
from sqlalchemy import Dialect, Engine, String, TypeDecorator, create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase
from src.core.constants import RESERVED_TAG_END

logger = structlog.getLogger(__name__)


class PathType(TypeDecorator):
    impl = String
    cache_ok = True

    def process_bind_param(self, value: Path, dialect: Dialect):
        if value is not None:
            return Path(value).as_posix()
        return None

    def process_result_value(self, value: str, dialect: Dialect):
        if value is not None:
            return Path(value)
        return None


class Base(DeclarativeBase):
    type_annotation_map = {Path: PathType}


def make_engine(connection_string: str) -> Engine:
    return create_engine(connection_string)


def make_tables(engine: Engine) -> None:
    logger.info("[Library] Creating DB tables...")
    Base.metadata.create_all(engine)

    # tag IDs < 1000 are reserved
    # create tag and delete it to bump the autoincrement sequence
    # TODO - find a better way
    # is this the better way?
    with engine.connect() as conn:
        result = conn.execute(text("SELECT SEQ FROM sqlite_sequence WHERE name='tags'"))
        autoincrement_val = result.scalar()
        if not autoincrement_val or autoincrement_val <= RESERVED_TAG_END:
            try:
                conn.execute(
                    text(
                        "INSERT INTO tags "
                        "(id, name, color_namespace, color_slug, is_category) VALUES "
                        f"({RESERVED_TAG_END}, 'temp', NULL, NULL, false)"
                    )
                )
                conn.execute(text(f"DELETE FROM tags WHERE id = {RESERVED_TAG_END}"))
                conn.commit()
            except OperationalError as e:
                logger.error("Could not initialize built-in tags", error=e)
                conn.rollback()


def drop_tables(engine: Engine) -> None:
    logger.info("dropping db tables")
    Base.metadata.drop_all(engine)
