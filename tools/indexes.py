from __future__ import annotations

from typing import Any

from db.mysql_inspector import MySQLInspector


def get_indexes(
    sql: str,
    database: str | None = None,
    tables: list[str] | None = None,
) -> dict[str, Any]:
    """获取 SQL 涉及表的 MySQL 索引信息。"""
    # tables 允许调用方手动指定表名，用来处理复杂 SQL、CTE、子查询等自动解析不准的情况。
    return MySQLInspector(database=database).get_indexes(sql, tables=tables)
