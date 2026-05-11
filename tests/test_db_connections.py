from __future__ import annotations

import os
import unittest

import pyodbc

from sql_performance_mcp.db.connection import (
    mysql_connection,
    postgresql_connection,
    sqlserver_connection,
)


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


def _resolve_sqlserver_driver() -> str:
    preferred = ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"]
    available = set(pyodbc.drivers())
    for driver in preferred:
        if driver in available:
            return driver
    raise unittest.SkipTest("No SQL Server ODBC driver is installed.")


class DatabaseConnectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not SQLSERVER_TEST_CONFIG["driver"]:
            SQLSERVER_TEST_CONFIG["driver"] = _resolve_sqlserver_driver()
        cls._prepare_sqlserver_database()

    def test_mysql_connection_success(self) -> None:
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
                cursor.execute("SELECT 1 AS value")
                row = cursor.fetchone()
        self.assertEqual(row["value"], 1)

    def test_postgresql_connection_success(self) -> None:
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
                cursor.execute("SELECT 1 AS value")
                row = cursor.fetchone()
        self.assertEqual(row["value"], 1)

    def test_sqlserver_connection_success(self) -> None:
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

        with sqlserver_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 AS value")
                row = cursor.fetchone()
        self.assertEqual(row[0], 1)

    @classmethod
    def _prepare_sqlserver_database(cls) -> None:
        os.environ.update(
            {
                "SQLSERVER_HOST": SQLSERVER_TEST_CONFIG["host"],
                "SQLSERVER_PORT": str(SQLSERVER_TEST_CONFIG["port"]),
                "SQLSERVER_USER": SQLSERVER_TEST_CONFIG["user"],
                "SQLSERVER_PASSWORD": SQLSERVER_TEST_CONFIG["password"],
                "SQLSERVER_DRIVER": SQLSERVER_TEST_CONFIG["driver"] or "",
            }
        )

        with sqlserver_connection(database="master") as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "IF DB_ID(N'%s') IS NULL BEGIN EXEC('CREATE DATABASE [%s]') END"
                    % (SQLSERVER_TEST_CONFIG["database"], SQLSERVER_TEST_CONFIG["database"])
                )


if __name__ == "__main__":
    unittest.main()
