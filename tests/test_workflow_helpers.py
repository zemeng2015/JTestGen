import unittest

from javatestgen.workflow import clean_java_source


class WorkflowHelperTests(unittest.TestCase):
    def test_clean_java_source_removes_markdown_fence(self) -> None:
        self.assertEqual(
            clean_java_source("```java\nclass ExampleTest {}\n```"),
            "class ExampleTest {}",
        )


if __name__ == "__main__":
    unittest.main()
