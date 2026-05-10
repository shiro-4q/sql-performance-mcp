from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from tools.analyze import analyze_performance as build_performance_analysis_prompt
from tools.execution_plan import get_execution_plan as fetch_execution_plan
from tools.indexes import get_indexes as fetch_indexes
from tools.schema import get_table_schema as fetch_table_schema


# FastMCP 会把下面装饰过的方法暴露给 MCP 客户端。
mcp = FastMCP("sql-performance-mcp")


@mcp.tool()
def get_execution_plan(sql: str, database: str | None = None) -> dict[str, Any]:
    """获取 MySQL 执行计划，优先使用 EXPLAIN FORMAT=JSON。"""
    return fetch_execution_plan(sql=sql, database=database)


@mcp.tool()
def get_table_schema(
    sql: str,
    database: str | None = None,
    tables: list[str] | None = None,
) -> dict[str, Any]:
    """获取 SQL 涉及表的表结构。复杂 SQL 可以显式传 tables。"""
    return fetch_table_schema(sql=sql, database=database, tables=tables)


@mcp.tool()
def get_indexes(
    sql: str,
    database: str | None = None,
    tables: list[str] | None = None,
) -> dict[str, Any]:
    """获取 SQL 涉及表的索引信息。复杂 SQL 可以显式传 tables。"""
    return fetch_indexes(sql=sql, database=database, tables=tables)


@mcp.tool()
def analyze_performance(sql: str, execution_plan: str, schema: str, indexes: str) -> str:
    """组装 SQL 性能分析 prompt。"""
    return build_performance_analysis_prompt(
        sql=sql,
        execution_plan=execution_plan,
        schema=schema,
        indexes=indexes,
        database_type="MySQL",
    )


if __name__ == "__main__":
    mcp.run()
