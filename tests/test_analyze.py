import unittest

from tools.analyze import analyze_performance


class AnalyzeTests(unittest.TestCase):
    def test_analyze_performance_formats_structured_context(self) -> None:
        prompt = analyze_performance(
            sql="select * from users where id = 1",
            execution_plan={"plan": {"table": "users"}},
            schema={"app.users": {"columns": [{"COLUMN_NAME": "id"}]}},
            indexes={"app.users": [{"name": "PRIMARY"}]},
        )

        self.assertIn("你是 MySQL 性能优化专家。", prompt)
        self.assertIn("select * from users where id = 1", prompt)
        self.assertIn('"table": "users"', prompt)
        self.assertIn('"COLUMN_NAME": "id"', prompt)
        self.assertIn('"name": "PRIMARY"', prompt)


if __name__ == "__main__":
    unittest.main()
