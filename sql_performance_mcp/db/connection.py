from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterator, Any

if TYPE_CHECKING:  # pragma: no cover - imported only for type checkers.
    from pymysql.connections import Connection


@dataclass(frozen=True)
class MySQLConfig:
    host: str
    port: int
    user: str
    password: str
    database: str | None = None
    charset: str = "utf8mb4"
    connect_timeout: int = 10

    @classmethod
    def from_env(cls, database: str | None = None) -> "MySQLConfig":
        return cls(
            host=os.getenv("MYSQL_HOST", "127.0.0.1"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=database or os.getenv("MYSQL_DATABASE"),
            charset=os.getenv("MYSQL_CHARSET", "utf8mb4"),
            connect_timeout=int(os.getenv("MYSQL_CONNECT_TIMEOUT", "10")),
        )


@dataclass(frozen=True)
class PostgreSQLConfig:
    host: str
    port: int
    user: str
    password: str
    database: str | None = None
    connect_timeout: int = 10
    sslmode: str | None = None

    @classmethod
    def from_env(cls, database: str | None = None) -> "PostgreSQLConfig":
        return cls(
            host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
            database=database or os.getenv("POSTGRES_DATABASE"),
            connect_timeout=int(os.getenv("POSTGRES_CONNECT_TIMEOUT", "10")),
            sslmode=os.getenv("POSTGRES_SSLMODE"),
        )


@dataclass(frozen=True)
class SQLServerConfig:
    host: str
    port: int
    user: str
    password: str
    database: str | None = None
    driver: str = "ODBC Driver 18 for SQL Server"
    dsn: str | None = None
    encrypt: str = "yes"
    trust_server_certificate: str = "yes"
    connect_timeout: int = 10

    @classmethod
    def from_env(cls, database: str | None = None) -> "SQLServerConfig":
        return cls(
            host=os.getenv("SQLSERVER_HOST", "127.0.0.1"),
            port=int(os.getenv("SQLSERVER_PORT", "1433")),
            user=os.getenv("SQLSERVER_USER", "sa"),
            password=os.getenv("SQLSERVER_PASSWORD", ""),
            database=database or os.getenv("SQLSERVER_DATABASE"),
            driver=os.getenv("SQLSERVER_DRIVER", "ODBC Driver 18 for SQL Server"),
            dsn=os.getenv("SQLSERVER_DSN"),
            encrypt=os.getenv("SQLSERVER_ENCRYPT", "yes"),
            trust_server_certificate=os.getenv("SQLSERVER_TRUST_SERVER_CERTIFICATE", "yes"),
            connect_timeout=int(os.getenv("SQLSERVER_CONNECT_TIMEOUT", "10")),
        )


@contextmanager
def mysql_connection(database: str | None = None) -> Iterator[Connection]:
    import pymysql

    config = MySQLConfig.from_env(database=database)
    connection = pymysql.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        database=config.database,
        charset=config.charset,
        connect_timeout=config.connect_timeout,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )
    try:
        yield connection
    finally:
        connection.close()


def _load_psycopg() -> tuple[object, object]:
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:  # pragma: no cover - exercised only when optional deps are missing.
        raise RuntimeError("PostgreSQL support requires psycopg to be installed.") from exc
    return psycopg, dict_row


def _load_pyodbc() -> object:
    try:
        import pyodbc
    except ImportError as exc:  # pragma: no cover - exercised only when optional deps are missing.
        raise RuntimeError("SQL Server support requires pyodbc to be installed.") from exc
    return pyodbc


@contextmanager
def postgresql_connection(database: str | None = None) -> Iterator[object]:
    psycopg, dict_row = _load_psycopg()
    config = PostgreSQLConfig.from_env(database=database)
    connection_kwargs = {
        "host": config.host,
        "port": config.port,
        "user": config.user,
        "password": config.password,
        "dbname": config.database,
        "connect_timeout": config.connect_timeout,
        "row_factory": dict_row,
        "autocommit": True,
    }
    if config.sslmode:
        connection_kwargs["sslmode"] = config.sslmode
    connection = psycopg.connect(**connection_kwargs)
    try:
        yield connection
    finally:
        connection.close()


def _build_sqlserver_connection_string(config: SQLServerConfig) -> str:
    parts: list[str] = []
    if config.dsn:
        parts.append(f"DSN={config.dsn}")
    else:
        parts.append(f"DRIVER={{{config.driver}}}")
        parts.append(f"SERVER={config.host},{config.port}")
    if config.database:
        parts.append(f"DATABASE={config.database}")
    if config.user:
        parts.append(f"UID={config.user}")
    if config.password:
        parts.append(f"PWD={config.password}")
    if "odbc driver" in config.driver.lower():
        parts.append(f"Encrypt={config.encrypt}")
        parts.append(f"TrustServerCertificate={config.trust_server_certificate}")
    parts.append(f"Connection Timeout={config.connect_timeout}")
    return ";".join(parts)


@contextmanager
def sqlserver_connection(database: str | None = None) -> Iterator[object]:
    pyodbc = _load_pyodbc()
    config = SQLServerConfig.from_env(database=database)
    connection = pyodbc.connect(
        _build_sqlserver_connection_string(config),
        autocommit=True,
        timeout=config.connect_timeout,
    )
    try:
        yield connection
    finally:
        connection.close()

