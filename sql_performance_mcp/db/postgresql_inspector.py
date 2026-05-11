from __future__ import annotations

import json
from typing import Any

from .common import first_value, fetch_rows_as_dicts
from .connection import postgresql_connection
from .queries import ensure_single_statement, extract_table_names, split_table_name


class PostgreSQLInspector:
    def __init__(self, database: str | None = None) -> None:
        self.database = database

    def get_execution_plan(self, sql: str) -> dict[str, Any]:
        statement = ensure_single_statement(sql)
        with postgresql_connection(self.database) as connection:
            with connection.cursor() as cursor:
                try:
                    cursor.execute(f"EXPLAIN (FORMAT JSON) {statement}")
                    row = cursor.fetchone()
                    plan = first_value(row)
                    if isinstance(plan, str):
                        try:
                            plan = json.loads(plan)
                        except json.JSONDecodeError:
                            pass
                    return {
                        "database_type": "postgresql",
                        "database": self.database,
                        "format": "json",
                        "plan": plan,
                    }
                except Exception as json_error:
                    cursor.execute(f"EXPLAIN {statement}")
                    return {
                        "database_type": "postgresql",
                        "database": self.database,
                        "format": "tabular",
                        "plan": fetch_rows_as_dicts(cursor),
                        "json_error": str(json_error),
                    }

    def get_table_schema(self, sql: str, tables: list[str] | None = None) -> dict[str, Any]:
        table_names = tables or extract_table_names(sql)
        if not table_names:
            raise ValueError("No table names were found. Pass tables explicitly for complex SQL.")

        with postgresql_connection(self.database) as connection:
            current_schema = self._current_schema(connection)
            result: dict[str, Any] = {}
            with connection.cursor() as cursor:
                for raw_table in table_names:
                    schema_name, table_name = split_table_name(raw_table, current_schema)
                    if not schema_name:
                        raise ValueError("POSTGRES_DATABASE or an explicit schema is required.")

                    cursor.execute(
                        """
                        SELECT
                            column_name,
                            data_type,
                            udt_name,
                            is_nullable,
                            column_default,
                            character_maximum_length,
                            numeric_precision,
                            numeric_scale,
                            datetime_precision,
                            collation_name
                        FROM information_schema.columns
                        WHERE table_schema = %s AND table_name = %s
                        ORDER BY ordinal_position
                        """,
                        (schema_name, table_name),
                    )
                    result[f"{schema_name}.{table_name}"] = {"columns": fetch_rows_as_dicts(cursor)}
            return result

    def get_indexes(self, sql: str, tables: list[str] | None = None) -> dict[str, Any]:
        table_names = tables or extract_table_names(sql)
        if not table_names:
            raise ValueError("No table names were found. Pass tables explicitly for complex SQL.")

        with postgresql_connection(self.database) as connection:
            current_schema = self._current_schema(connection)
            result: dict[str, Any] = {}
            with connection.cursor() as cursor:
                for raw_table in table_names:
                    schema_name, table_name = split_table_name(raw_table, current_schema)
                    if not schema_name:
                        raise ValueError("POSTGRES_DATABASE or an explicit schema is required.")

                    cursor.execute(
                        """
                        SELECT
                            indexname AS index_name,
                            indexdef AS index_definition
                        FROM pg_indexes
                        WHERE schemaname = %s AND tablename = %s
                        ORDER BY indexname
                        """,
                        (schema_name, table_name),
                    )
                    rows = fetch_rows_as_dicts(cursor)
                    result[f"{schema_name}.{table_name}"] = self._format_indexes(rows)
            return result

    def _current_schema(self, connection: Any) -> str | None:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_schema() AS schema_name")
            row = cursor.fetchone()
            return first_value(row)

    @staticmethod
    def _format_indexes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        indexes: list[dict[str, Any]] = []
        for row in rows:
            definition = row["index_definition"]
            indexes.append(
                {
                    "name": row["index_name"],
                    "unique": definition.upper().startswith("CREATE UNIQUE INDEX"),
                    "definition": definition,
                }
            )
        return indexes
