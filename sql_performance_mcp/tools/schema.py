from __future__ import annotations

from typing import Any

from ..db.factory import get_inspector


def get_table_schema(
    sql: str,
    database: str | None = None,
    tables: list[str] | None = None,
    database_type: str | None = None,
) -> dict[str, Any]:
    return get_inspector(database_type=database_type, database=database).get_table_schema(sql, tables=tables)

