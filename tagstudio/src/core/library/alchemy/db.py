from pathlib import Path

import structlog
from sqlalchemy import Dialect, Engine, String, TypeDecorator, create_engine, text
from sqlalchemy.orm import DeclarativeBase

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
    logger.info("creating db tables")
    Base.metadata.create_all(engine)

    # tag IDs < 1000 are reserved
    # create tag and delete it to bump the autoincrement sequence
    # TODO - find a better way
    with engine.connect() as conn:
        conn.execute(text("INSERT INTO tags (id, name, color) VALUES (999, 'temp', 1)"))
        conn.execute(text("DELETE FROM tags WHERE id = 999"))
        conn.commit()


def drop_tables(engine: Engine) -> None:
    logger.info("dropping db tables")
    Base.metadata.drop_all(engine)
