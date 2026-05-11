from __future__ import annotations

import os
import unittest
from dataclasses import dataclass
from typing import Any

import pyodbc

from sql_performance_mcp.db.connection import mysql_connection, postgresql_connection, sqlserver_connection
from sql_performance_mcp.tools.execution_plan import get_execution_plan
from sql_performance_mcp.tools.indexes import get_indexes
from sql_performance_mcp.tools.schema import get_table_schema


MYSQL_TEST_CONFIG = {
    "host": os.getenv("TEST_MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("TEST_MYSQL_PORT", "3307")),
    "user": os.getenv("TEST_MYSQL_USER", "root"),
    "password": os.getenv("TEST_MYSQL_PASSWORD", "SqlPerf!2345"),
    "database": os.getenv("TEST_MYSQL_DATABASE", "app_db"),
}

POSTGRES_TEST_CONFIG = {
    "host": os.getenv("TEST_POSTGRES_HOST", "127.0.0.1"),
    "port": int(os.getenv("TEST_POSTGRES_PORT", "15432")),
    "user": os.getenv("TEST_POSTGRES_USER", "postgres"),
    "password": os.getenv("TEST_POSTGRES_PASSWORD", "SqlPerf!2345"),
    "database": os.getenv("TEST_POSTGRES_DATABASE", "app_db"),
}

SQLSERVER_TEST_CONFIG = {
    "host": os.getenv("TEST_SQLSERVER_HOST", "127.0.0.1"),
    "port": int(os.getenv("TEST_SQLSERVER_PORT", "11433")),
    "user": os.getenv("TEST_SQLSERVER_USER", "sa"),
    "password": os.getenv("TEST_SQLSERVER_PASSWORD", "SqlPerf!2345"),
    "database": os.getenv("TEST_SQLSERVER_DATABASE", "app_db"),
    "driver": os.getenv("TEST_SQLSERVER_DRIVER"),
}

SQLSERVER_DRIVER_PREFERENCE = ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"]


@dataclass(frozen=True)
class ToolTestTarget:
    database_type: str
    database: str
    table_name: str
    qualified_table_name: str
    select_sql: str


def _resolve_sqlserver_driver() -> str:
    available = set(pyodbc.drivers())
    for driver in SQLSERVER_DRIVER_PREFERENCE:
        if driver in available:
            return driver
    raise unittest.SkipTest("No SQL Server ODBC driver is installed.")


def _row_value(row: Any) -> Any:
    if row is None:
        return None
    if isinstance(row, dict):
        return next(iter(row.values())) if row else None
    return row[0]


class DatabaseToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not SQLSERVER_TEST_CONFIG["driver"]:
            SQLSERVER_TEST_CONFIG["driver"] = _resolve_sqlserver_driver()
        cls.mysql_target = cls._prepare_mysql_target()
        cls.postgres_target = cls._prepare_postgres_target()
        cls.sqlserver_target = cls._prepare_sqlserver_target()

    def test_mysql_tools_success(self) -> None:
        self._assert_tool_triplet(self.mysql_target)

    def test_postgresql_tools_success(self) -> None:
        self._assert_tool_triplet(self.postgres_target)

    def test_sqlserver_tools_success(self) -> None:
        self._assert_tool_triplet(self.sqlserver_target)

    def _assert_tool_triplet(self, target: ToolTestTarget) -> None:
        plan = get_execution_plan(
            sql=target.select_sql,
            database=target.database,
            database_type=target.database_type,
        )
        schema = get_table_schema(
            sql=target.select_sql,
            database=target.database,
            tables=[target.qualified_table_name],
            database_type=target.database_type,
        )
        indexes = get_indexes(
            sql=target.select_sql,
            database=target.database,
            tables=[target.qualified_table_name],
            database_type=target.database_type,
        )

        self.assertEqual(plan["database_type"], target.database_type)
        self.assertIn("plan", plan)
        self.assertIn(target.qualified_table_name, schema)
        self.assertIn("columns", schema[target.qualified_table_name])
        self.assertTrue(schema[target.qualified_table_name]["columns"])
        self.assertIn(target.qualified_table_name, indexes)
        self.assertIsInstance(indexes[target.qualified_table_name], list)

    @classmethod
    def _prepare_mysql_target(cls) -> ToolTestTarget:
        os.environ.update(
            {
                "MYSQL_HOST": MYSQL_TEST_CONFIG["host"],
                "MYSQL_PORT": str(MYSQL_TEST_CONFIG["port"]),
                "MYSQL_USER": MYSQL_TEST_CONFIG["user"],
                "MYSQL_PASSWORD": MYSQL_TEST_CONFIG["password"],
                "MYSQL_DATABASE": MYSQL_TEST_CONFIG["database"],
            }
        )
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT TABLE_NAME
                    FROM information_schema.TABLES
                    WHERE TABLE_SCHEMA = %s
                      AND TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_NAME
                    LIMIT 1
                    """,
                    (MYSQL_TEST_CONFIG["database"],),
                )
                row = cursor.fetchone()
                if row:
                    table_name = row["TABLE_NAME"]
                else:
                    table_name = "sqlperf_tool_test"
                    cursor.execute(
                        f"""
                        CREATE TABLE IF NOT EXISTS `{table_name}` (
                            id INT NOT NULL PRIMARY KEY,
                            name VARCHAR(64) NOT NULL
                        )
                        """
                    )
                    cursor.execute(f"INSERT INTO `{table_name}` (id, name) VALUES (1, 'alpha') ON DUPLICATE KEY UPDATE name = VALUES(name)")
        qualified_table_name = f"{MYSQL_TEST_CONFIG['database']}.{table_name}"
        select_sql = f"SELECT * FROM `{MYSQL_TEST_CONFIG['database']}`.`{table_name}` LIMIT 1"
        return ToolTestTarget("mysql", MYSQL_TEST_CONFIG["database"], table_name, qualified_table_name, select_sql)

    @classmethod
    def _prepare_postgres_target(cls) -> ToolTestTarget:
        os.environ.update(
            {
                "POSTGRES_HOST": POSTGRES_TEST_CONFIG["host"],
                "POSTGRES_PORT": str(POSTGRES_TEST_CONFIG["port"]),
                "POSTGRES_USER": POSTGRES_TEST_CONFIG["user"],
                "POSTGRES_PASSWORD": POSTGRES_TEST_CONFIG["password"],
                "POSTGRES_DATABASE": POSTGRES_TEST_CONFIG["database"],
            }
        )
        with postgresql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = current_schema()
                      AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                    LIMIT 1
                    """
                )
                row = cursor.fetchone()
                if row:
                    table_name = row["table_name"]
                else:
                    table_name = "sqlperf_tool_test"
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS sqlperf_tool_test (
                            id INTEGER PRIMARY KEY,
                            name TEXT NOT NULL
                        )
                        """
                    )
                    cursor.execute(
                        "INSERT INTO sqlperf_tool_test (id, name) VALUES (1, 'alpha') ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name"
                    )
        qualified_table_name = f"public.{table_name}"
        select_sql = f'SELECT * FROM public."{table_name}" LIMIT 1'
        return ToolTestTarget("postgresql", POSTGRES_TEST_CONFIG["database"], table_name, qualified_table_name, select_sql)

    @classmethod
    def _prepare_sqlserver_target(cls) -> ToolTestTarget:
        os.environ.update(
            {
                "SQLSERVER_HOST": SQLSERVER_TEST_CONFIG["host"],
                "SQLSERVER_PORT": str(SQLSERVER_TEST_CONFIG["port"]),
                "SQLSERVER_USER": SQLSERVER_TEST_CONFIG["user"],
                "SQLSERVER_PASSWORD": SQLSERVER_TEST_CONFIG["password"],
                "SQLSERVER_DATABASE": SQLSERVER_TEST_CONFIG["database"],
                "SQLSERVER_DRIVER": SQLSERVER_TEST_CONFIG["driver"],
            }
        )
        with sqlserver_connection(database="master") as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "IF DB_ID(N'%s') IS NULL BEGIN EXEC('CREATE DATABASE [%s]') END"
                    % (SQLSERVER_TEST_CONFIG["database"], SQLSERVER_TEST_CONFIG["database"])
                )
        with sqlserver_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT TABLE_NAME
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_SCHEMA = 'dbo'
                      AND TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_NAME
                    """
                )
                row = cursor.fetchone()
                if row:
                    table_name = row[0]
                else:
                    table_name = "sqlperf_tool_test"
                    cursor.execute(
                        """
                        IF OBJECT_ID(N'dbo.sqlperf_tool_test', N'U') IS NULL
                        BEGIN
                            CREATE TABLE dbo.sqlperf_tool_test (
                                id INT NOT NULL PRIMARY KEY,
                                name NVARCHAR(64) NOT NULL
                            )
                        END
                        """
                    )
                    cursor.execute(
                        """
                        IF NOT EXISTS (SELECT 1 FROM dbo.sqlperf_tool_test WHERE id = 1)
                        INSERT INTO dbo.sqlperf_tool_test (id, name) VALUES (1, N'alpha')
                        """
                    )
        qualified_table_name = f"dbo.{table_name}"
        select_sql = f"SELECT TOP 1 * FROM [dbo].[{table_name}]"
        return ToolTestTarget("sqlserver", SQLSERVER_TEST_CONFIG["database"], table_name, qualified_table_name, select_sql)


if __name__ == "__main__":
    unittest.main()
