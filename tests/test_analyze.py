# unittest 是 Python 标准库自带的测试框架。
# 它可以帮我们组织测试用例、执行测试，并检查结果是否符合预期。
import unittest

# 导入要测试的函数。
from sql_performance_mcp.tools.analyze import analyze_performance


# 继承 unittest.TestCase，表示这是一个测试类。
# 测试框架会自动识别里面以 test_ 开头的方法，把它们当成测试用例执行。
class AnalyzeTests(unittest.TestCase):
    # -> None 表示这个测试方法本身不返回有用结果。
    # 测试是否通过，取决于里面的断言有没有失败，而不是 return 什么值。
    def test_analyze_performance_formats_structured_context(self) -> None:
        # 调用被测试函数，构造一个最小但完整的输入场景。
        prompt = analyze_performance(
            sql="select * from users where id = 1",
            execution_plan={"plan": {"table": "users"}},
            schema={"app.users": {"columns": [{"COLUMN_NAME": "id"}]}},
            indexes={"app.users": [{"name": "PRIMARY"}]},
        )

        # self.assertIn(a, b) 的意思是：断言 a 出现在 b 里面。
        # 如果 a 不在 b 中，这个测试就会失败。
        # 这里是在验证 analyze_performance 返回的 prompt 是否包含关键上下文信息。
        self.assertIn("You are a MySQL performance optimization expert.", prompt)
        self.assertIn("select * from users where id = 1", prompt)
        self.assertIn('"table": "users"', prompt)
        self.assertIn('"COLUMN_NAME": "id"', prompt)
        self.assertIn('"name": "PRIMARY"', prompt)


# __name__ == "__main__" 是 Python 常见写法：
# 当这个文件被“直接运行”时，下面的代码会执行；
# 当它被别的文件 import 时，下面的代码不会执行。
if __name__ == "__main__":
    # unittest.main() 会自动发现并运行当前文件中的测试。
    unittest.main()
