from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .tools.analyze import analyze_performance as build_performance_analysis_prompt
from .tools.execution_plan import get_execution_plan as fetch_execution_plan
from .tools.indexes import get_indexes as fetch_indexes
from .tools.schema import get_table_schema as fetch_table_schema

mcp = FastMCP("sql-performance-mcp")


@mcp.tool()
def get_execution_plan(sql: str, database: str | None = None) -> dict[str, Any]:
    """Fetch a MySQL execution plan."""
    return fetch_execution_plan(sql=sql, database=database)


@mcp.tool()
def get_table_schema(
    sql: str,
    database: str | None = None,
    tables: list[str] | None = None,
) -> dict[str, Any]:
    """Fetch table schema metadata for the SQL statement."""
    return fetch_table_schema(sql=sql, database=database, tables=tables)


@mcp.tool()
def get_indexes(
    sql: str,
    database: str | None = None,
    tables: list[str] | None = None,
) -> dict[str, Any]:
    """Fetch index metadata for the SQL statement."""
    return fetch_indexes(sql=sql, database=database, tables=tables)


@mcp.tool()
def analyze_performance(sql: str, execution_plan: str, schema: str, indexes: str) -> str:
    """Build a MySQL performance analysis prompt."""
    return build_performance_analysis_prompt(
        sql=sql,
        execution_plan=execution_plan,
        schema=schema,
        indexes=indexes,
        database_type="MySQL",
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

