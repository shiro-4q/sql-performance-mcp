# 让类型注解延迟解析。简单理解：下面可以先把类型当作“说明文字”保存，
# 避免某些类型在运行到这一行时还没定义好而报错。
from __future__ import annotations

# os 是 Python 标准库，用来读取操作系统相关信息；这里主要读取环境变量。
import os
# contextmanager 是一个装饰器，可以把带 yield 的函数变成 with 语句可用的上下文管理器。
from contextlib import contextmanager
# dataclass 可以帮我们自动生成 __init__ 等方法，适合定义“只保存数据”的类。
from dataclasses import dataclass
# Iterator 是类型注解，表示这个函数会“产出”某种类型的对象。
from typing import Iterator

# pymysql 是第三方包，用来让 Python 连接并操作 MySQL。
import pymysql
# Connection 是 pymysql 里的连接对象类型，这里只用于类型注解，让代码更容易读。
from pymysql.connections import Connection


# @xxx 这种写法叫“装饰器”：它会在类或函数定义完成后，对它做一层加工。
# dataclass 会根据下面声明的字段，自动生成构造方法，例如 MySQLConfig(host=..., port=...)。
# frozen=True 表示对象创建后字段不能再被修改，适合保存数据库连接配置这种不希望中途变化的数据。
@dataclass(frozen=True)
class MySQLConfig:
    """MySQL 连接配置，统一从环境变量或调用参数里收口。"""

    # 冒号后面的 str、int 是“类型注解”，不会强制转换类型，主要给人和编辑器看。
    # 例如 host: str 表示 host 应该是字符串。
    host: str
    port: int
    user: str
    password: str
    # str | None 表示这个值可以是字符串，也可以是 None。
    # 这是 Optional[str] 的新写法；= None 表示默认值是 None。
    database: str | None = None
    # utf8mb4 是 MySQL 常用字符集，支持中文和 emoji。
    charset: str = "utf8mb4"
    # 连接超时时间，单位通常是秒。
    connect_timeout: int = 10

    # @classmethod 表示这是“类方法”，调用时不需要先创建对象：
    # MySQLConfig.from_env()
    # 普通实例方法第一个参数通常是 self，代表“当前对象”；
    # 类方法第一个参数通常写 cls，代表“当前类”，这里的 cls 基本可以理解为 MySQLConfig。
    @classmethod
    def from_env(cls, database: str | None = None) -> "MySQLConfig":
        """从环境变量构造连接配置；方法参数 database 优先级高于 MYSQL_DATABASE。"""
        # return cls(...) 表示创建并返回一个 MySQLConfig 对象。
        # 这里不用直接写 MySQLConfig(...)，是因为 cls 在类方法里更灵活，方便以后继承。
        return cls(
            # os.getenv("变量名", "默认值")：读取环境变量；如果没有，就使用默认值。
            host=os.getenv("MYSQL_HOST", "127.0.0.1"),
            # 环境变量读出来都是字符串，所以端口要用 int(...) 转成整数。
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            # a or b 是常见简写：如果 a 有值就用 a，否则用 b。
            # 所以传入的 database 会优先于环境变量 MYSQL_DATABASE。
            database=database or os.getenv("MYSQL_DATABASE"),
            charset=os.getenv("MYSQL_CHARSET", "utf8mb4"),
            connect_timeout=int(os.getenv("MYSQL_CONNECT_TIMEOUT", "10")),
        )


# @contextmanager 也是装饰器。它把 mysql_connection 变成可以这样使用的函数：
# with mysql_connection() as connection:
#     ...
# with 代码块结束时，finally 里的 close 会自动执行。
@contextmanager
def mysql_connection(database: str | None = None) -> Iterator[Connection]:
    """创建 MySQL 连接，并确保工具调用结束后关闭连接。"""
    # 先根据环境变量和参数生成连接配置。
    config = MySQLConfig.from_env(database=database)
    # pymysql.connect(...) 会真正建立到 MySQL 的连接。
    connection = pymysql.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        database=config.database,
        charset=config.charset,
        connect_timeout=config.connect_timeout,
        # DictCursor 让查询结果直接是 dict，例如 {"id": 1, "name": "Tom"}。
        # 这比普通 tuple 结果更适合 MCP 工具输出 JSON。
        cursorclass=pymysql.cursors.DictCursor,
        # 这个项目主要执行 EXPLAIN、读取表结构、读取索引等检查类 SQL，
        # 通常不需要手动事务；自动提交可以避免连接一直持有事务状态。
        autocommit=True,
    )
    try:
        # yield 会把 connection 暂时交给 with 代码块使用。
        # 等 with 代码块执行完，会回到这里继续执行 finally。
        yield connection
    finally:
        # finally 表示无论上面是否报错，最后都会执行这里的代码。
        # 数据库连接属于外部资源，用完一定要关闭。
        connection.close()
