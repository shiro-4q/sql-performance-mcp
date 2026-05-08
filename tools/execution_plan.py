from __future__ import annotations

from typing import Any

from db.mysql_inspector import MySQLInspector


def get_execution_plan(sql: str, database: str | None = None) -> dict[str, Any]:
    """获取单条 SQL 的 MySQL 优化器执行计划。"""
    return MySQLInspector(database=database).get_execution_plan(sql)
