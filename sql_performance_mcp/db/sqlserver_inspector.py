from __future__ import annotations

from typing import Any

from .common import first_value, fetch_rows_as_dicts
from .connection import sqlserver_connection
from .queries import ensure_single_statement, extract_table_names, split_table_name


class SQLServerInspector:
    def __init__(self, database: str | None = None) -> None:
        self.database = database

    def get_execution_plan(self, sql: str) -> dict[str, Any]:
        statement = ensure_single_statement(sql)
        with sqlserver_connection(self.database) as connection:
            with connection.cursor() as cursor:
                try:
                    cursor.execute("SET SHOWPLAN_XML ON")
                    cursor.execute(statement)
                    row = cursor.fetchone()
                    return {
                        "database_type": "sqlserver",
                        "database": self.database,
                        "format": "xml",
                        "plan": first_value(row),
                    }
                except Exception as xml_error:
                    try:
                        cursor.execute("SET SHOWPLAN_TEXT ON")
                        cursor.execute(statement)
                        return {
                            "database_type": "sqlserver",
                            "database": self.database,
                            "format": "text",
                            "plan": fetch_rows_as_dicts(cursor),
                            "xml_error": str(xml_error),
                        }
                    finally:
                        try:
                            cursor.execute("SET SHOWPLAN_TEXT OFF")
                        except Exception:
                            pass
                finally:
                    try:
                        cursor.execute("SET SHOWPLAN_XML OFF")
                    except Exception:
                        pass

    def get_table_schema(self, sql: str, tables: list[str] | None = None) -> dict[str, Any]:
        table_names = tables or extract_table_names(sql)
        if not table_names:
            raise ValueError("No table names were found. Pass tables explicitly for complex SQL.")

        with sqlserver_connection(self.database) as connection:
            current_schema = self._current_schema(connection)
            result: dict[str, Any] = {}
            with connection.cursor() as cursor:
                for raw_table in table_names:
                    schema_name, table_name = split_table_name(raw_table, current_schema)
                    if not schema_name:
                        raise ValueError("SQLSERVER_DATABASE or an explicit schema is required.")

                    cursor.execute(
                        """
                        SELECT
                            COLUMN_NAME AS column_name,
                            DATA_TYPE AS data_type,
                            IS_NULLABLE AS is_nullable,
                            COLUMN_DEFAULT AS column_default,
                            CHARACTER_MAXIMUM_LENGTH AS character_maximum_length,
                            NUMERIC_PRECISION AS numeric_precision,
                            NUMERIC_SCALE AS numeric_scale,
                            DATETIME_PRECISION AS datetime_precision,
                            COLLATION_NAME AS collation_name
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
                        ORDER BY ORDINAL_POSITION
                        """,
                        (schema_name, table_name),
                    )
                    result[f"{schema_name}.{table_name}"] = {"columns": fetch_rows_as_dicts(cursor)}
            return result

    def get_indexes(self, sql: str, tables: list[str] | None = None) -> dict[str, Any]:
        table_names = tables or extract_table_names(sql)
        if not table_names:
            raise ValueError("No table names were found. Pass tables explicitly for complex SQL.")

        with sqlserver_connection(self.database) as connection:
            current_schema = self._current_schema(connection)
            result: dict[str, Any] = {}
            with connection.cursor() as cursor:
                for raw_table in table_names:
                    schema_name, table_name = split_table_name(raw_table, current_schema)
                    if not schema_name:
                        raise ValueError("SQLSERVER_DATABASE or an explicit schema is required.")

                    cursor.execute(
                        """
                        SELECT
                            i.name AS index_name,
                            i.is_unique AS is_unique,
                            i.is_primary_key AS is_primary_key,
                            i.type_desc AS index_type,
                            ic.key_ordinal AS key_ordinal,
                            ic.is_included_column AS is_included_column,
                            c.name AS column_name
                        FROM sys.indexes i
                        JOIN sys.tables t ON i.object_id = t.object_id
                        JOIN sys.schemas s ON t.schema_id = s.schema_id
                        LEFT JOIN sys.index_columns ic
                            ON i.object_id = ic.object_id AND i.index_id = ic.index_id
                        LEFT JOIN sys.columns c
                            ON ic.object_id = c.object_id AND ic.column_id = c.column_id
                        WHERE s.name = ? AND t.name = ? AND i.name IS NOT NULL
                        ORDER BY i.name, ic.key_ordinal, c.column_id
                        """,
                        (schema_name, table_name),
                    )
                    result[f"{schema_name}.{table_name}"] = self._format_indexes(fetch_rows_as_dicts(cursor))
            return result

    def _current_schema(self, connection: Any) -> str | None:
        with connection.cursor() as cursor:
            cursor.execute("SELECT SCHEMA_NAME() AS schema_name")
            row = cursor.fetchone()
            return first_value(row)

    @staticmethod
    def _format_indexes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, dict[str, Any]] = {}
        for row in rows:
            index_name = row["index_name"]
            index = grouped.setdefault(
                index_name,
                {
                    "name": index_name,
                    "unique": bool(row["is_unique"]),
                    "primary": bool(row["is_primary_key"]),
                    "type": row["index_type"],
                    "columns": [],
                },
            )
            if row["column_name"]:
                index["columns"].append(
                    {
                        "seq": row["key_ordinal"],
                        "name": row["column_name"],
                        "included": bool(row["is_included_column"]),
                    }
                )
        return list(grouped.values())
