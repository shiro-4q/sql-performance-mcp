from __future__ import annotations

import os
from typing import Any

from .mysql_inspector import MySQLInspector
from .postgresql_inspector import PostgreSQLInspector
from .sqlserver_inspector import SQLServerInspector

_DATABASE_TYPE_ALIASES = {
    "mysql": "mysql",
    "mariadb": "mysql",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "pgsql": "postgresql",
    "pg": "postgresql",
    "sqlserver": "sqlserver",
    "sql_server": "sqlserver",
    "mssql": "sqlserver",
    "sql server": "sqlserver",
}

_DATABASE_TYPE_LABELS = {
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "sqlserver": "SQL Server",
}


def normalize_database_type(database_type: str | None = None) -> str:
    value = database_type or os.getenv("SQL_PERFORMANCE_DB_TYPE") or os.getenv("DB_TYPE") or "mysql"
    normalized = value.strip().lower()
    return _DATABASE_TYPE_ALIASES.get(normalized, normalized)


def database_type_label(database_type: str | None = None) -> str:
    normalized = normalize_database_type(database_type)
    return _DATABASE_TYPE_LABELS.get(normalized, normalized.title())


def get_inspector(database_type: str | None = None, database: str | None = None) -> Any:
    normalized = normalize_database_type(database_type)
    if normalized == "mysql":
        return MySQLInspector(database=database)
    if normalized == "postgresql":
        return PostgreSQLInspector(database=database)
    if normalized == "sqlserver":
        return SQLServerInspector(database=database)
    supported = ", ".join(sorted(_DATABASE_TYPE_LABELS.values()))
    raise ValueError(f"Unsupported database type: {database_type!r}. Supported types: {supported}.")
