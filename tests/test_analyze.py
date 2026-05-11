import unittest

from sql_performance_mcp.tools.analyze import analyze_performance


class AnalyzeTests(unittest.TestCase):
    def test_analyze_performance_formats_structured_context(self) -> None:
        prompt = analyze_performance(
            sql="select * from users where id = 1",
            execution_plan={"plan": {"table": "users"}},
            schema={"app.users": {"columns": [{"COLUMN_NAME": "id"}]}},
            indexes={"app.users": [{"name": "PRIMARY"}]},
        )

        self.assertIn("You are a MySQL performance optimization expert.", prompt)
        self.assertIn("select * from users where id = 1", prompt)
        self.assertIn('"table": "users"', prompt)
        self.assertIn('"COLUMN_NAME": "id"', prompt)
        self.assertIn('"name": "PRIMARY"', prompt)

    def test_analyze_performance_uses_database_label(self) -> None:
        prompt = analyze_performance(
            sql="select 1",
            execution_plan={},
            schema={},
            indexes={},
            database_type="postgresql",
        )

        self.assertIn("You are a PostgreSQL performance optimization expert.", prompt)


if __name__ == "__main__":
    unittest.main()
