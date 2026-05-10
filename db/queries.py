# 让类型注解延迟解析。这个文件里影响不大，但和项目其他文件保持一致。
from __future__ import annotations

# re 是 Python 标准库里的“正则表达式”模块，常用于字符串匹配、提取、替换。
import re


# 变量名前面的单下划线是一种约定，表示“模块内部使用”的常量或函数。
# 这里定义了一个正则片段，用来匹配 SQL 里的“标识符”，也就是库名、表名、列名这类名字。
#
# r"..." 叫“原始字符串”（raw string）：
# 里面的反斜杠 \ 不会被 Python 当成转义字符先处理，特别适合写正则。
#
# (?:...) 是“非捕获分组”：
# 它只负责分组，不会像普通 (...) 那样单独保存一个 match 分组结果。
#
# 这个表达式的意思大致是：
# 1. 要么匹配被反引号包起来的名字，例如 `users`
# 2. 要么匹配普通名字，例如 users、app_db、user$log
_IDENTIFIER = r"(?:`[^`]+`|[A-Za-z_][\w$]*)"

# rf"..." 同时具备两种能力：
# 1. r: 原始字符串，方便写正则
# 2. f: 格式化字符串，可以把前面定义的变量插进来
#
# 这个表达式的意思是：
# 先匹配一个标识符，然后“可选地”再匹配 . 和第二个标识符。
# 所以它既能匹配 users，也能匹配 app.users。
#
# \s* 表示“零个或多个空白字符”
# \. 表示字面量的小数点 .
# (...) ? 最后的 ? 表示“这一整组内容可以出现 0 次或 1 次”
_QUALIFIED_IDENTIFIER = rf"{_IDENTIFIER}(?:\s*\.\s*{_IDENTIFIER})?"

# 轻量解析常见 SQL 里的表名；复杂 SQL 可由调用方显式传 tables。
# re.compile(...) 会把正则表达式预编译，后面重复使用时更方便。
_TABLE_PATTERN = re.compile(
    # \b 表示“单词边界”，避免误匹配到别的单词的一部分。
    # (?:from|join|update|into) 表示匹配其中任意一个关键字。
    # \s+ 表示一个或多个空白字符。
    # (...) 这里是普通捕获分组，后面会用 match.group(1) 取出匹配到的表名。
    rf"\b(?:from|join|update|into)\s+({_QUALIFIED_IDENTIFIER})",
    # re.IGNORECASE 表示忽略大小写，所以 FROM/from/From 都能匹配。
    re.IGNORECASE,
)


def strip_identifier_quotes(identifier: str) -> str:
    """去掉 MySQL 反引号，便于拼 information_schema 查询条件。"""
    # identifier.strip() 会去掉字符串两端的空白字符。
    # 再 .strip("`") 会去掉字符串两端的反引号。
    # 例如 "  `users`  " -> "users"
    return identifier.strip().strip("`")


def split_table_name(table_name: str, default_schema: str | None = None) -> tuple[str | None, str]:
    """把 app.users 或 users 拆成 (schema, table)。"""
    # re.split(...) 是“按正则切分字符串”。
    # r"\s*\.\s*" 的意思是：按点号 . 切分，并允许点号两边有空格。
    # maxsplit=1 表示最多只切一次，避免出现超过两段。
    #
    # [ ... for part in ... ] 是“列表推导式”，是简洁写法。
    # 等价于：
    # parts = []
    # for part in re.split(...):
    #     parts.append(strip_identifier_quotes(part))
    parts = [strip_identifier_quotes(part) for part in re.split(r"\s*\.\s*", table_name, maxsplit=1)]
    if len(parts) == 2:
        return parts[0], parts[1]
    # 如果没有显式 schema，就返回默认 schema 和表名。
    return default_schema, parts[0]


def extract_table_names(sql: str) -> list[str]:
    """从 SQL 中提取表名，覆盖 FROM/JOIN/UPDATE/INSERT INTO 这类常见场景。"""
    # 创建一个空列表，准备存放提取到的表名。
    tables: list[str] = []
    # finditer(...) 会返回一个可迭代对象，里面每个元素都是一个匹配结果 match。
    for match in _TABLE_PATTERN.finditer(sql):
        # match.group(1) 取出正则里第 1 个捕获分组，也就是表名部分。
        # re.sub(r"\s+", "", ...) 会把所有空白字符替换为空字符串。
        # 例如 "app . users" 会被整理成 "app.users"
        table_name = re.sub(r"\s+", "", match.group(1))
        # lower() 转成小写，startswith(...) 判断是否以某些前缀开头。
        # 这里传入的是一个元组，所以只要以 "select" 或 "with" 开头都算匹配。
        # 遇到子查询或 CTE 时，正则可能抓到 SELECT/WITH，这里直接跳过。
        if table_name.lower().startswith(("select", "with")):
            continue
        # 只有当表名还没出现过时才加入，避免重复。
        if table_name not in tables:
            tables.append(table_name)
    return tables


def ensure_single_statement(sql: str) -> str:
    """限制为单条 SQL，避免 EXPLAIN 被拼接额外语句。"""
    # strip() 去掉首尾空格、换行等空白字符。
    normalized = sql.strip()
    if not normalized:
        raise ValueError("SQL must not be empty.")

    # 这是条件表达式，等价于：
    # if normalized.endswith(";"):
    #     statement = normalized[:-1].strip()
    # else:
    #     statement = normalized
    #
    # normalized[:-1] 表示“从开头切到倒数第 1 个字符之前”，也就是去掉最后一个字符。
    # 这里的目的，是允许 SQL 最后带一个分号，但会把这个结尾分号去掉。
    statement = normalized[:-1].strip() if normalized.endswith(";") else normalized
    # 如果处理中间还存在分号，说明大概率不止一条 SQL，例如：
    # SELECT * FROM users; DELETE FROM users;
    if ";" in statement:
        raise ValueError("Only a single SQL statement is supported.")
    return statement
