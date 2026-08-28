# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


from sqlite3 import Connection


def list_tables(con: Connection) -> list[str]:
    cur = con.cursor()
    res = cur.execute("SELECT name FROM sqlite_master WHERE type == 'table';")
    return [row[0] for row in res.fetchall()]
