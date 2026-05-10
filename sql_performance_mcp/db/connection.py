from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

import pymysql
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


@contextmanager
def mysql_connection(database: str | None = None) -> Iterator[Connection]:
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

