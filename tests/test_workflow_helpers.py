import unittest

from javatestgen.workflow import clean_java_source, format_new_file_patch


class WorkflowHelperTests(unittest.TestCase):
    def test_clean_java_source_removes_markdown_fence(self) -> None:
        self.assertEqual(
            clean_java_source("```java\nclass ExampleTest {}\n```"),
            "class ExampleTest {}",
        )

    def test_format_new_file_patch_outputs_reviewable_diff(self) -> None:
        patch = format_new_file_patch("src/test/java/com/example/ExampleTest.java", "class ExampleTest {}\n")

        self.assertIn("diff --git a/src/test/java/com/example/ExampleTest.java b/src/test/java/com/example/ExampleTest.java", patch)
        self.assertIn("--- /dev/null", patch)
        self.assertIn("+++ b/src/test/java/com/example/ExampleTest.java", patch)
        self.assertIn("+class ExampleTest {}", patch)


if __name__ == "__main__":
    unittest.main()
