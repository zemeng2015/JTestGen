import tempfile
import unittest
from pathlib import Path

from javatestgen.context import find_existing_target_test, find_sample_tests, infer_test_package, load_rules
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
            (other_package / "OtherTest.java").write_text("import org.junit.jupiter.api.Test; class OtherTest { @Test void ok() {} }", encoding="utf-8")
            (same_package / "OrderServiceTest.java").write_text("import org.junit.jupiter.api.Test; class OrderServiceTest { @Test void ok() {} }", encoding="utf-8")
            target = JavaClass(
                source_path=Path("OrderService.java"),
                relative_path=Path("com/example/OrderService.java"),
                source="",
                package="com.example",
                type_name="OrderService",
            )

            samples = find_sample_tests(test_root, target, 1)

        self.assertEqual(samples[0].path.name, "OrderServiceTest.java")

    def test_ignores_manual_test_files_without_test_annotation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            test_root = Path(temp_dir) / "src" / "test" / "java"
            package_dir = test_root / "com" / "example"
            package_dir.mkdir(parents=True)
            (package_dir / "ManualPerfTest.java").write_text("class ManualPerfTest { public static void main(String[] args) {} }", encoding="utf-8")
            (package_dir / "RealTest.java").write_text("import org.junit.jupiter.api.Test; class RealTest { @Test void ok() {} }", encoding="utf-8")
            target = JavaClass(
                source_path=Path("Thing.java"),
                relative_path=Path("com/example/Thing.java"),
                source="",
                package="com.example",
                type_name="Thing",
            )

            samples = find_sample_tests(test_root, target, 3)

        self.assertEqual([sample.path.name for sample in samples], ["RealTest.java"])

    def test_sample_selection_excludes_generated_target_test(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            test_root = Path(temp_dir) / "src" / "test" / "java"
            package_dir = test_root / "com" / "example"
            package_dir.mkdir(parents=True)
            generated = package_dir / "ThingGeneratedTest.java"
            generated.write_text("import org.junit.jupiter.api.Test; class ThingGeneratedTest { @Test void old() {} }", encoding="utf-8")
            (package_dir / "ThingStyleTest.java").write_text("import org.junit.jupiter.api.Test; class ThingStyleTest { @Test void ok() {} }", encoding="utf-8")
            target = JavaClass(
                source_path=Path("Thing.java"),
                relative_path=Path("com/example/Thing.java"),
                source="",
                package="com.example",
                type_name="Thing",
            )

            samples = find_sample_tests(test_root, target, 3, generated)

        self.assertEqual([sample.path.name for sample in samples], ["ThingStyleTest.java"])

    def test_finds_existing_target_test(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "ThingGeneratedTest.java"
            path.write_text("class ThingGeneratedTest {}", encoding="utf-8")

            existing = find_existing_target_test(path)

        self.assertIsNotNone(existing)
        self.assertEqual(existing.source, "class ThingGeneratedTest {}")

    def test_infers_test_package_from_nearest_sample(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            test_root = Path(temp_dir) / "src" / "test" / "java"
            package_dir = test_root / "tools" / "jackson" / "core" / "unittest" / "io"
            package_dir.mkdir(parents=True)
            (package_dir / "BufferRecyclerPoolTest.java").write_text(
                "package tools.jackson.core.unittest.io;\nimport org.junit.jupiter.api.Test; class BufferRecyclerPoolTest { @Test void ok() {} }",
                encoding="utf-8",
            )
            target = JavaClass(
                source_path=Path("DataOutputAsStream.java"),
                relative_path=Path("tools/jackson/core/io/DataOutputAsStream.java"),
                source="",
                package="tools.jackson.core.io",
                type_name="DataOutputAsStream",
            )
            generated = test_root / "tools" / "jackson" / "core" / "io" / "DataOutputAsStreamGeneratedTest.java"

            test_package = infer_test_package(test_root, target, generated)

        self.assertEqual(test_package, "tools.jackson.core.unittest.io")


if __name__ == "__main__":
    unittest.main()
