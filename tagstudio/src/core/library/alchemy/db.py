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
            ('#1e1e1e', 'DEFAULT', TRUE),
            ('#111018', 'BLACK', TRUE),
            ('#24232a', 'DARK_GRAY', TRUE),
            ('#53525a', 'GRAY', TRUE),
            ('#aaa9b0', 'LIGHT_GRAY', TRUE),
            ('#f2f1f8', 'WHITE', TRUE),
            ('#ff99c4', 'LIGHT_PINK', TRUE),
            ('#ff99c4', 'PINK', TRUE),
            ('#f6466f', 'MAGENTA', TRUE),
            ('#e22c3c', 'RED', TRUE),
            ('#e83726', 'RED_ORANGE', TRUE),
            ('#f65848', 'SALMON', TRUE),
            ('#ed6022', 'ORANGE', TRUE),
            ('#fa9a2c', 'YELLOW_ORANGE', TRUE),
            ('#ffd63d', 'YELLOW', TRUE),
            ('#4aed90', 'MINT', TRUE),
            ('#92e649', 'LIME', TRUE),
            ('#85ec76', 'LIGHT_GREEN', TRUE),
            ('#28bb48', 'GREEN', TRUE),
            ('#1ad9b2', 'TEAL', TRUE),
            ('#49e4d5', 'CYAN', TRUE),
            ('#55bbf6', 'LIGHT_BLUE', TRUE),
            ('#3b87f0', 'BLUE', TRUE),
            ('#5948f2', 'BLUE_VIOLET', TRUE),
            ('#874ff5', 'VIOLET', TRUE),
            ('#bb4ff0', 'PURPLE', TRUE),
            ('#f1c69c', 'PEACH', TRUE),
            ('#823216', 'BROWN', TRUE),
            ('#ad8eef', 'LAVENDER', TRUE),
            ('#efc664', 'BLONDE', TRUE),
            ('#a13220', 'AUBURN', TRUE),
            ('#be5b2d', 'LIGHT_BROWN', TRUE),
            ('#4c2315', 'DARK_BROWN', TRUE),
            ('#515768', 'COOL_GRAY', TRUE),
            ('#625550', 'WARM_GRAY', TRUE),
            ('#4c652e', 'OLIVE', TRUE),
            ('#9f2aa7', 'BERRY', TRUE)"""
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
