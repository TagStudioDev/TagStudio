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

        conn.execute(
            text(
                """INSERT INTO user_defined_colors (color, name, user_defined) VALUES
            ('#1e1e1e', 'DEFAULT', FALSE),
            ('#111018', 'BLACK', FALSE),
            ('#24232a', 'DARK_GRAY', FALSE),
            ('#53525a', 'GRAY', FALSE),
            ('#aaa9b0', 'LIGHT_GRAY', FALSE),
            ('#f2f1f8', 'WHITE', FALSE),
            ('#ff99c4', 'LIGHT_PINK', FALSE),
            ('#ff99c4', 'PINK', FALSE),
            ('#f6466f', 'MAGENTA', FALSE),
            ('#e22c3c', 'RED', FALSE),
            ('#e83726', 'RED_ORANGE', FALSE),
            ('#f65848', 'SALMON', FALSE),
            ('#ed6022', 'ORANGE', FALSE),
            ('#fa9a2c', 'YELLOW_ORANGE', FALSE),
            ('#ffd63d', 'YELLOW', FALSE),
            ('#4aed90', 'MINT', FALSE),
            ('#92e649', 'LIME', FALSE),
            ('#85ec76', 'LIGHT_GREEN', FALSE),
            ('#28bb48', 'GREEN', FALSE),
            ('#1ad9b2', 'TEAL', FALSE),
            ('#49e4d5', 'CYAN', FALSE),
            ('#55bbf6', 'LIGHT_BLUE', FALSE),
            ('#3b87f0', 'BLUE', FALSE),
            ('#5948f2', 'BLUE_VIOLET', FALSE),
            ('#874ff5', 'VIOLET', FALSE),
            ('#bb4ff0', 'PURPLE', FALSE),
            ('#f1c69c', 'PEACH', FALSE),
            ('#823216', 'BROWN', FALSE),
            ('#ad8eef', 'LAVENDER', FALSE),
            ('#efc664', 'BLONDE', FALSE),
            ('#a13220', 'AUBURN', FALSE),
            ('#be5b2d', 'LIGHT_BROWN', FALSE),
            ('#4c2315', 'DARK_BROWN', FALSE),
            ('#515768', 'COOL_GRAY', FALSE),
            ('#625550', 'WARM_GRAY', FALSE),
            ('#4c652e', 'OLIVE', FALSE),
            ('#9f2aa7', 'BERRY', FALSE)"""
            )
        )

        conn.execute(
            text(
                """
            CREATE TRIGGER delete_color BEFORE DELETE ON user_defined_colors
            WHEN OLD.user_defined = FALSE
            BEGIN
                SELECT RAISE(ABORT, 'Cannot delete program-defined colors');
            END;
            """
            )
        )
        conn.commit()


def drop_tables(engine: Engine) -> None:
    logger.info("dropping db tables")
    Base.metadata.drop_all(engine)
