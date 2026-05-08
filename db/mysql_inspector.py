from __future__ import annotations

import json
from typing import Any

from db.connection import mysql_connection
from db.queries import ensure_single_statement, extract_table_names, split_table_name


class MySQLInspector:
    """封装 MySQL 元数据与执行计划读取逻辑，后续扩展其他数据库时可做同类 Inspector。"""

    def __init__(self, database: str | None = None) -> None:
        """database 为可选库名；不传时读取 MYSQL_DATABASE 或当前连接默认库。"""
        self.database = database

    def get_execution_plan(self, sql: str) -> dict[str, Any]:
        """获取 SQL 执行计划，优先返回 MySQL JSON 格式。"""
        statement = ensure_single_statement(sql)
        with mysql_connection(self.database) as connection:
            with connection.cursor() as cursor:
                try:
                    # JSON 格式更适合大模型分析，也方便后续程序化处理。
                    cursor.execute(f"EXPLAIN FORMAT=JSON {statement}")
                    row = cursor.fetchone()
                    plan = next(iter(row.values())) if row else None
                    return {
                        "database": self.database,
                        "format": "json",
                        "plan": json.loads(plan) if isinstance(plan, str) else plan,
                    }
                except Exception as json_error:
                    # 老版本 MySQL 或部分语句可能不支持 FORMAT=JSON，退回普通 EXPLAIN。
                    cursor.execute(f"EXPLAIN {statement}")
                    return {
                        "database": self.database,
                        "format": "tabular",
                        "plan": cursor.fetchall(),
                        "json_error": str(json_error),
                    }

    def get_table_schema(self, sql: str, tables: list[str] | None = None) -> dict[str, Any]:
        """获取 SQL 涉及表的字段信息。"""
        table_names = tables or extract_table_names(sql)
        if not table_names:
            raise ValueError("No table names were found. Pass tables explicitly for complex SQL.")

        with mysql_connection(self.database) as connection:
            current_database = self._current_database(connection)
            result: dict[str, Any] = {}
            with connection.cursor() as cursor:
                for raw_table in table_names:
                    # information_schema 需要明确 schema/table；没有库名时用当前连接库。
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
                    columns = cursor.fetchall()
                    result[f"{schema_name}.{table_name}"] = {"columns": columns}
            return result

    def get_indexes(self, sql: str, tables: list[str] | None = None) -> dict[str, Any]:
        """获取 SQL 涉及表的索引信息。"""
        table_names = tables or extract_table_names(sql)
        if not table_names:
            raise ValueError("No table names were found. Pass tables explicitly for complex SQL.")

        with mysql_connection(self.database) as connection:
            current_database = self._current_database(connection)
            result: dict[str, Any] = {}
            with connection.cursor() as cursor:
                for raw_table in table_names:
                    # 同一张表的索引可能包含多列，后面会按 INDEX_NAME 聚合。
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
        """获取当前连接默认库，用于处理调用方只传 users 这种未带库名的表。"""
        if self.database:
            return self.database
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE() AS database_name")
            row = cursor.fetchone()
            return row["database_name"] if row else None

    @staticmethod
    def _group_indexes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """把 information_schema.STATISTICS 的逐列结果聚合成逐索引结构。"""
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
