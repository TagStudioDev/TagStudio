# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from sqlite3 import Connection


def list_tables(con: Connection) -> list[str]:
    return [
        row[0]
        for row in con.execute("SELECT name FROM sqlite_master WHERE type == 'table'").fetchall()
    ]
