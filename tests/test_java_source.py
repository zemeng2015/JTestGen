import tempfile
import unittest
from pathlib import Path

from javatestgen.java_source import discover_java_classes


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


if __name__ == "__main__":
    unittest.main()
