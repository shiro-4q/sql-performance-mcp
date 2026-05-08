from __future__ import annotations

from typing import Any

from db.mysql_inspector import MySQLInspector


def get_table_schema(
    sql: str,
    database: str | None = None,
    tables: list[str] | None = None,
) -> dict[str, Any]:
    """获取 SQL 涉及表的字段元数据。"""
    # tables 可选：复杂 SQL 自动解析不准时，调用方可以显式指定表名列表。
    return MySQLInspector(database=database).get_table_schema(sql, tables=tables)
