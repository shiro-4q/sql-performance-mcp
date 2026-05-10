from __future__ import annotations

import json
from typing import Any

from .connection import mysql_connection
from .queries import ensure_single_statement, extract_table_names, split_table_name


class MySQLInspector:
    def __init__(self, database: str | None = None) -> None:
        self.database = database

    def get_execution_plan(self, sql: str) -> dict[str, Any]:
        statement = ensure_single_statement(sql)
        with mysql_connection(self.database) as connection:
            with connection.cursor() as cursor:
                try:
                    cursor.execute(f"EXPLAIN FORMAT=JSON {statement}")
                    row = cursor.fetchone()
                    plan = next(iter(row.values())) if row else None
                    return {
                        "database": self.database,
                        "format": "json",
                        "plan": json.loads(plan) if isinstance(plan, str) else plan,
                    }
                except Exception as json_error:
                    cursor.execute(f"EXPLAIN {statement}")
                    return {
                        "database": self.database,
                        "format": "tabular",
                        "plan": cursor.fetchall(),
                        "json_error": str(json_error),
                    }

    def get_table_schema(self, sql: str, tables: list[str] | None = None) -> dict[str, Any]:
        table_names = tables or extract_table_names(sql)
        if not table_names:
            raise ValueError("No table names were found. Pass tables explicitly for complex SQL.")

        with mysql_connection(self.database) as connection:
            current_database = self._current_database(connection)
            result: dict[str, Any] = {}
            with connection.cursor() as cursor:
                for raw_table in table_names:
                    schema_name, table_name = split_table_name(raw_table, current_database)
                    if not schema_name:
                        raise ValueError("MYSQL_DATABASE or an explicit database is required.")

                    cursor.execute(
                        """
                        SELECT
                            COLUMN_NAME,
                            COLUMN_TYPE,
                            IS_NULLABLE,
                            COLUMN_DEFAULT,
                            COLUMN_KEY,
                            EXTRA,
                            COLUMN_COMMENT
                        FROM information_schema.COLUMNS
                        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                        ORDER BY ORDINAL_POSITION
                        """,
                        (schema_name, table_name),
                    )
                    result[f"{schema_name}.{table_name}"] = {"columns": cursor.fetchall()}
            return result

    def get_indexes(self, sql: str, tables: list[str] | None = None) -> dict[str, Any]:
        table_names = tables or extract_table_names(sql)
        if not table_names:
            raise ValueError("No table names were found. Pass tables explicitly for complex SQL.")

        with mysql_connection(self.database) as connection:
            current_database = self._current_database(connection)
            result: dict[str, Any] = {}
            with connection.cursor() as cursor:
                for raw_table in table_names:
                    schema_name, table_name = split_table_name(raw_table, current_database)
                    if not schema_name:
                        raise ValueError("MYSQL_DATABASE or an explicit database is required.")

                    cursor.execute(
                        """
                        SELECT
                            INDEX_NAME,
                            NON_UNIQUE,
                            SEQ_IN_INDEX,
                            COLUMN_NAME,
                            COLLATION,
                            CARDINALITY,
                            INDEX_TYPE,
                            INDEX_COMMENT
                        FROM information_schema.STATISTICS
                        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                        ORDER BY INDEX_NAME, SEQ_IN_INDEX
                        """,
                        (schema_name, table_name),
                    )
                    result[f"{schema_name}.{table_name}"] = self._group_indexes(cursor.fetchall())
            return result

    def _current_database(self, connection: Any) -> str | None:
        if self.database:
            return self.database
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE() AS database_name")
            row = cursor.fetchone()
            return row["database_name"] if row else None

    @staticmethod
    def _group_indexes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, dict[str, Any]] = {}
        for row in rows:
            index_name = row["INDEX_NAME"]
            index = grouped.setdefault(
                index_name,
                {
                    "name": index_name,
                    "unique": row["NON_UNIQUE"] == 0,
                    "type": row["INDEX_TYPE"],
                    "comment": row["INDEX_COMMENT"],
                    "columns": [],
                },
            )
            index["columns"].append(
                {
                    "seq": row["SEQ_IN_INDEX"],
                    "name": row["COLUMN_NAME"],
                    "collation": row["COLLATION"],
                    "cardinality": row["CARDINALITY"],
                }
            )
        return list(grouped.values())

