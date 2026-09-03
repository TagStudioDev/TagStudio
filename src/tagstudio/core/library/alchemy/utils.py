# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from sqlite3 import Connection

from sqlalchemy import inspect

from tagstudio.core.library.alchemy.db import Base


def list_tables(con: Connection) -> list[str]:
    return [
        row[0]
        for row in con.execute("SELECT name FROM sqlite_master WHERE type == 'table'").fetchall()
    ]


def sqlqlchemy_to_dict(obj: Base) -> dict:
    mapper = inspect(obj.__class__)
    return {col.name: getattr(obj, col.name) for col in mapper.columns}
