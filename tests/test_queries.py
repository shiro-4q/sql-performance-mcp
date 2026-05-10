# unittest 是 Python 标准库自带的测试框架。
import unittest

# 导入要测试的函数。
from sql_performance_mcp.db.queries import ensure_single_statement, extract_table_names, split_table_name


class QueryTests(unittest.TestCase):
    def test_extract_table_names_from_select_with_join(self) -> None:
        # 三引号字符串适合写多行文本，这里用来写多行 SQL。
        sql = """
        SELECT u.id, o.id
        FROM `app`.`users` u
        JOIN orders o ON o.user_id = u.id
        WHERE u.status = 'active'
        """

        # assertEqual(a, b) 表示断言 a 和 b 相等。
        # 这里验证 extract_table_names 是否能从带 JOIN 的查询中提取出表名。
        self.assertEqual(extract_table_names(sql), ["`app`.`users`", "orders"])

    def test_split_table_name_uses_default_schema(self) -> None:
        # 第一个断言：当只传表名 users，且默认库名是 app 时，
        # 应该得到 ("app", "users")。
        self.assertEqual(split_table_name("users", "app"), ("app", "users"))
        # 第二个断言：当传入带反引号的完整表名时，
        # 应该去掉反引号，并拆成 schema 和 table 两部分。
        self.assertEqual(split_table_name("`app`.`users`"), ("app", "users"))

    def test_ensure_single_statement_rejects_multiple_statements(self) -> None:
        # with self.assertRaises(ValueError) 的意思是：
        # 下面这段代码“应该抛出 ValueError 异常”。
        # 如果没有抛出，或者抛出了别的异常，这个测试都会失败。
        with self.assertRaises(ValueError):
            ensure_single_statement("select 1; select 2")


if __name__ == "__main__":
    unittest.main()
