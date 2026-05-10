# 让类型注解延迟解析，便于在注解里引用稍后定义的类型，也让类型注解更像“说明信息”。
from __future__ import annotations

# json 是 Python 标准库，用来把 JSON 字符串转成 Python 对象，或反过来转换。
import json
# Any 表示“任意类型”。当返回结果可能是多种形态时，经常会先用 Any 做宽松标注。
from typing import Any

# 从 db.connection 导入我们前面讲过的数据库连接上下文管理器。
from db.connection import mysql_connection
# 这些函数来自 db.queries，用来提前处理 SQL 文本。
# ensure_single_statement: 确保只传入一条 SQL，避免多语句带来的歧义和风险。
# extract_table_names: 尝试从 SQL 中提取表名。
# split_table_name: 把 app.users 这种名字拆成 schema 和 table 两部分。
from db.queries import ensure_single_statement, extract_table_names, split_table_name


class MySQLInspector:
    """封装 MySQL 元数据与执行计划读取逻辑，后续扩展其他数据库时可做同类 Inspector。"""

    # __init__ 是“构造方法”，创建对象时会自动调用。
    # 例如 inspector = MySQLInspector("app_db") 时，这个方法就会执行。
    # -> None 表示这个方法本身不返回有用结果；它的作用是初始化对象。
    def __init__(self, database: str | None = None) -> None:
        """database 为可选库名；不传时读取 MYSQL_DATABASE 或当前连接默认库。"""
        # self 代表“当前对象本身”。
        # self.database = database 表示把传进来的参数保存到对象里，供后续方法复用。
        self.database = database

    # 这个方法接收一条 SQL，返回一个字典。
    # dict[str, Any] 表示：字典的键是字符串，值可以是任意类型。
    def get_execution_plan(self, sql: str) -> dict[str, Any]:
        """获取 SQL 执行计划，优先返回 MySQL JSON 格式。"""
        # 先确保用户只传入一条 SQL。
        statement = ensure_single_statement(sql)
        # with mysql_connection(...) as connection:
        # 会打开数据库连接，并在 with 代码块结束时自动关闭连接。
        with mysql_connection(self.database) as connection:
            # connection.cursor() 会创建游标对象，游标负责执行 SQL 和取回结果。
            with connection.cursor() as cursor:
                try:
                    # f"...{statement}" 是 f-string，作用是把变量值插入字符串里。
                    # 这里最终会得到类似：EXPLAIN FORMAT=JSON SELECT * FROM users
                    # JSON 格式更适合大模型分析，也方便后续程序化处理。
                    cursor.execute(f"EXPLAIN FORMAT=JSON {statement}")
                    # fetchone() 表示取一行结果；因为 EXPLAIN FORMAT=JSON 通常只返回一行。
                    row = cursor.fetchone()
                    # row.values() 取出字典里的所有值。
                    # iter(...) 把这些值变成可迭代对象。
                    # next(...) 取出第一个值。
                    # if row else None 表示如果没有查到结果，就把 plan 设为 None。
                    plan = next(iter(row.values())) if row else None
                    # return {...} 表示返回一个字典结果。
                    return {
                        "database": self.database,
                        "format": "json",
                        # isinstance(plan, str) 用来判断 plan 是否是字符串。
                        # 如果是 JSON 字符串，就用 json.loads(...) 转成 Python 字典/列表。
                        # 如果已经不是字符串，就原样返回。
                        "plan": json.loads(plan) if isinstance(plan, str) else plan,
                    }
                except Exception as json_error:
                    # except Exception as json_error 的意思是：
                    # 如果 try 里的代码抛出任意普通异常，就先不要让程序直接崩掉，
                    # 而是把异常对象保存到 json_error 变量中，在这里做降级处理。
                    # 老版本 MySQL 或部分语句可能不支持 FORMAT=JSON，退回普通 EXPLAIN。
                    cursor.execute(f"EXPLAIN {statement}")
                    return {
                        "database": self.database,
                        "format": "tabular",
                        # fetchall() 表示取回所有结果行。
                        "plan": cursor.fetchall(),
                        # str(json_error) 会把异常对象转成可读的错误文本。
                        "json_error": str(json_error),
                    }

    # tables 参数可以手动传表名列表；如果不传，就尝试从 SQL 自动提取。
    # list[str] | None 表示：要么是字符串列表，要么是 None。
    def get_table_schema(self, sql: str, tables: list[str] | None = None) -> dict[str, Any]:
        """获取 SQL 涉及表的字段信息。"""
        # 如果 tables 有值就用 tables，否则调用 extract_table_names(sql)。
        table_names = tables or extract_table_names(sql)
        if not table_names:
            # raise ValueError(...) 表示主动抛出一个“值不合法”的异常。
            raise ValueError("No table names were found. Pass tables explicitly for complex SQL.")

        with mysql_connection(self.database) as connection:
            # self._current_database(connection) 调用的是当前类里的另一个辅助方法。
            current_database = self._current_database(connection)
            # 先创建一个空字典，用来逐步装结果。
            result: dict[str, Any] = {}
            with connection.cursor() as cursor:
                # for ... in ... 是遍历写法：依次处理 table_names 里的每个表名。
                for raw_table in table_names:
                    # information_schema 需要明确 schema/table；没有库名时用当前连接库。
                    # split_table_name(...) 会返回两个值，所以左边用两个变量接收。
                    schema_name, table_name = split_table_name(raw_table, current_database)
                    if not schema_name:
                        raise ValueError("MYSQL_DATABASE or an explicit database is required.")

                    # cursor.execute 的第二个参数是 SQL 参数元组。
                    # %s 是 pymysql 的占位符写法，不是 Python 自己的字符串格式化。
                    # 这样写比手动拼 SQL 更安全。
                    cursor.execute(
                        # 三引号字符串允许写多行文本，这里很适合放 SQL。
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
                    # f"{schema_name}.{table_name}" 会拼出类似 "app.users" 这样的键。
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
                    # self._group_indexes(...) 会把“每行代表索引中的一列”这种结果，
                    # 整理成“每个索引一个对象，里面包含多个列”的结构。
                    result[f"{schema_name}.{table_name}"] = self._group_indexes(cursor.fetchall())
            return result

    # 这是一个辅助方法，名字以下划线开头，表示“类内部使用”为主。
    def _current_database(self, connection: Any) -> str | None:
        """获取当前连接默认库，用于处理调用方只传 users 这种未带库名的表。"""
        # 如果对象本身已经有 database，就直接返回，不再查数据库。
        if self.database:
            return self.database
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE() AS database_name")
            row = cursor.fetchone()
            # row["database_name"] if row else None 是条件表达式，等价于：
            # if row:
            #     return row["database_name"]
            # else:
            #     return None
            return row["database_name"] if row else None

    # @staticmethod 表示“静态方法”。
    # 它和类本身的状态无关，不需要 self，也不需要 cls。
    # 放在类里只是因为逻辑上它属于 MySQLInspector。
    @staticmethod
    def _group_indexes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """把 information_schema.STATISTICS 的逐列结果聚合成逐索引结构。"""
        # grouped 是一个字典：键是索引名，值是这个索引的汇总信息。
        grouped: dict[str, dict[str, Any]] = {}
        for row in rows:
            index_name = row["INDEX_NAME"]
            # dict.setdefault(key, default) 的意思是：
            # 如果 key 已存在，就返回已有值；
            # 如果 key 不存在，就先放入 default，再返回这个 default。
            index = grouped.setdefault(
                index_name,
                {
                    "name": index_name,
                    # NON_UNIQUE == 0 表示唯一索引，因此这里转成更好懂的 True/False。
                    "unique": row["NON_UNIQUE"] == 0,
                    "type": row["INDEX_TYPE"],
                    "comment": row["INDEX_COMMENT"],
                    "columns": [],
                },
            )
            # append(...) 表示把一个新元素追加到列表末尾。
            index["columns"].append(
                {
                    "seq": row["SEQ_IN_INDEX"],
                    "name": row["COLUMN_NAME"],
                    "collation": row["COLLATION"],
                    "cardinality": row["CARDINALITY"],
                }
            )
        # grouped.values() 取出所有值；list(...) 把它转成列表返回。
        return list(grouped.values())
