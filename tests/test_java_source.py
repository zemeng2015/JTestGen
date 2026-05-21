import tempfile
import unittest
from pathlib import Path

from javatestgen.java_source import discover_java_classes, find_java_class_by_name


class JavaSourceTests(unittest.TestCase):
    def test_discovers_public_class(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir) / "src" / "main" / "java"
            package_dir = source_root / "com" / "example"
            package_dir.mkdir(parents=True)
            (package_dir / "Calculator.java").write_text(
                "package com.example;\n\npublic class Calculator { int add(int a, int b) { return a + b; } }\n",
                encoding="utf-8",
            )

            classes = discover_java_classes(source_root, "**/*.java")

        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0].qualified_name, "com.example.Calculator")
        self.assertEqual(
            classes[0].test_relative_path("Test"),
            Path("com") / "example" / "CalculatorTest.java",
        )

    def test_finds_class_by_simple_or_qualified_name(self) -> None:
        java_class = self._java_class("com.example", "OrderService")

        self.assertIs(find_java_class_by_name([java_class], "OrderService"), java_class)
        self.assertIs(find_java_class_by_name([java_class], "com.example.OrderService"), java_class)

    def test_target_class_simple_name_must_not_be_ambiguous(self) -> None:
        first = self._java_class("com.example", "OrderService")
        second = self._java_class("org.example", "OrderService")

        with self.assertRaises(ValueError):
            find_java_class_by_name([first, second], "OrderService")

    def _java_class(self, package: str, type_name: str):
        from javatestgen.java_source import JavaClass

        return JavaClass(
            source_path=Path(f"{type_name}.java"),
            relative_path=Path(f"{type_name}.java"),
            source="",
            package=package,
            type_name=type_name,
        )


if __name__ == "__main__":
    unittest.main()
