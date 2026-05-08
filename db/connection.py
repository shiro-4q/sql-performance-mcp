from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

import pymysql
from pymysql.connections import Connection


@dataclass(frozen=True)
class MySQLConfig:
    """MySQL 连接配置，统一从环境变量或调用参数里收口。"""

    host: str
    port: int
    user: str
    password: str
    database: str | None = None
    charset: str = "utf8mb4"
    connect_timeout: int = 10

    @classmethod
    def from_env(cls, database: str | None = None) -> "MySQLConfig":
        """从环境变量构造连接配置；方法参数 database 优先级高于 MYSQL_DATABASE。"""
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
    """创建 MySQL 连接，并确保工具调用结束后关闭连接。"""
    config = MySQLConfig.from_env(database=database)
    connection = pymysql.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        database=config.database,
        charset=config.charset,
        connect_timeout=config.connect_timeout,
        # DictCursor 让返回值直接是 dict，MCP 工具输出 JSON 时更自然。
        cursorclass=pymysql.cursors.DictCursor,
        # 所有检查类 SQL 都不需要事务，自动提交可以避免连接持有事务状态。
        autocommit=True,
    )
    try:
        yield connection
    finally:
        connection.close()
