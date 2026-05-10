from __future__ import annotations

from typing import Any

from ..db.mysql_inspector import MySQLInspector


def get_execution_plan(sql: str, database: str | None = None) -> dict[str, Any]:
    return MySQLInspector(database=database).get_execution_plan(sql)

