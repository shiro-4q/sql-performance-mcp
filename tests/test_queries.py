import unittest

from db.queries import ensure_single_statement, extract_table_names, split_table_name


class QueryTests(unittest.TestCase):
    def test_extract_table_names_from_select_with_join(self) -> None:
        sql = """
        SELECT u.id, o.id
        FROM `app`.`users` u
        JOIN orders o ON o.user_id = u.id
        WHERE u.status = 'active'
        """

        self.assertEqual(extract_table_names(sql), ["`app`.`users`", "orders"])

    def test_split_table_name_uses_default_schema(self) -> None:
        self.assertEqual(split_table_name("users", "app"), ("app", "users"))
        self.assertEqual(split_table_name("`app`.`users`"), ("app", "users"))

    def test_ensure_single_statement_rejects_multiple_statements(self) -> None:
        with self.assertRaises(ValueError):
            ensure_single_statement("select 1; select 2")


if __name__ == "__main__":
    unittest.main()
