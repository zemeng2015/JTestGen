import tempfile
import unittest
from pathlib import Path

from javatestgen.context import find_sample_tests, load_rules
from javatestgen.java_source import JavaClass


class ContextTests(unittest.TestCase):
    def test_loads_project_rules_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            rules = project / "TESTGEN_RULES.md"
            rules.write_text("Use AssertJ.", encoding="utf-8")

            self.assertEqual(load_rules(project, None), "Use AssertJ.")

    def test_finds_same_package_sample_test_first(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            test_root = Path(temp_dir) / "src" / "test" / "java"
            same_package = test_root / "com" / "example"
            other_package = test_root / "org" / "example"
            same_package.mkdir(parents=True)
            other_package.mkdir(parents=True)
            (other_package / "OtherTest.java").write_text("class OtherTest {}", encoding="utf-8")
            (same_package / "OrderServiceTest.java").write_text("class OrderServiceTest {}", encoding="utf-8")
            target = JavaClass(
                source_path=Path("OrderService.java"),
                relative_path=Path("com/example/OrderService.java"),
                source="",
                package="com.example",
                type_name="OrderService",
            )

            samples = find_sample_tests(test_root, target, 1)

        self.assertEqual(samples[0].path.name, "OrderServiceTest.java")


if __name__ == "__main__":
    unittest.main()
