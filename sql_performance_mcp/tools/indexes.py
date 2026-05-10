from __future__ import annotations

from typing import Any

from ..db.mysql_inspector import MySQLInspector


def get_indexes(
    sql: str,
    database: str | None = None,
    tables: list[str] | None = None,
) -> dict[str, Any]:
    return MySQLInspector(database=database).get_indexes(sql, tables=tables)

