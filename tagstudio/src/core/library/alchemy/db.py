from pathlib import Path
from typing import Any

import structlog
from sqlalchemy import Dialect, Engine, String, TypeDecorator, create_engine
from sqlalchemy.orm import DeclarativeBase

logger = structlog.getLogger(__name__)


class PathType(TypeDecorator):
    impl = String
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Dialect):
        if value is not None:
            return str(value)
        return None

    def process_result_value(self, value: Any, dialect: Dialect):
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


def drop_tables(engine: Engine) -> None:
    logger.info("dropping db tables")
    Base.metadata.drop_all(engine)
