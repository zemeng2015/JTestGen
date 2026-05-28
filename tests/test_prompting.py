import unittest
from pathlib import Path

from javatestgen.context import PromptContext
from javatestgen.coverage import ClassCoverage
from javatestgen.java_source import JavaClass
from javatestgen.prompting import build_initial_request, build_repair_request


class PromptingTests(unittest.TestCase):
    def test_initial_prompt_includes_path_package_and_output_contract(self) -> None:
        request = build_initial_request(
            java_class=self._java_class(),
            test_class_name="ThingGeneratedTest",
            test_path="src/test/java/com/example/ThingGeneratedTest.java",
            coverage=self._coverage(),
            context=PromptContext(rules="Use JUnit 5.", sample_tests=[], related_sources=[], test_package="com.example.tests"),
        )

        self.assertIn("Generated test path: src/test/java/com/example/ThingGeneratedTest.java", request.user_prompt)
        self.assertIn("Use package `com.example.tests`.", request.user_prompt)
        self.assertIn("Return exactly one complete Java source file.", request.user_prompt)
        self.assertIn("Do not include Markdown fences", request.user_prompt)
        self.assertIn("Related production sources:", request.user_prompt)

    def test_repair_prompt_includes_exact_command_and_failure_guidance(self) -> None:
        request = build_repair_request(
            java_class=self._java_class(),
            current_test_source="package com.example; class ThingGeneratedTest {}",
            maven_output="[ERROR] cannot find symbol",
            test_class_name="ThingGeneratedTest",
            test_path="src/test/java/com/example/ThingGeneratedTest.java",
            test_command="mvn -q -DskipITs -Dtest=ThingGeneratedTest test",
            coverage=self._coverage(),
            context=PromptContext(rules="Use JUnit 5.", sample_tests=[], related_sources=[], test_package="com.example.tests"),
        )

        self.assertIn("mvn -q -DskipITs -Dtest=ThingGeneratedTest test", request.user_prompt)
        self.assertIn("First infer the failure category", request.user_prompt)
        self.assertIn("Java compilation error", request.user_prompt)
        self.assertIn("package exists in another module", request.user_prompt)
        self.assertIn("do not repeat the same wrong expected value", request.user_prompt)
        self.assertIn("update the expected assertion", request.user_prompt)
        self.assertIn("nothing was thrown", request.user_prompt)
        self.assertIn("do not create new resources or files", request.user_prompt)
        self.assertIn("UnnecessaryStubbingException", request.user_prompt)
        self.assertIn("Wanted but not invoked", request.user_prompt)
        self.assertIn("adjusted expected value", request.user_prompt)
        self.assertIn("Return exactly one complete corrected Java source file.", request.user_prompt)

    def _java_class(self) -> JavaClass:
        return JavaClass(
            source_path=Path("Thing.java"),
            relative_path=Path("com/example/Thing.java"),
            source="package com.example; public class Thing {}",
            package="com.example",
            type_name="Thing",
        )

    def _coverage(self) -> ClassCoverage:
        return ClassCoverage(
            qualified_name="com.example.Thing",
            package="com.example",
            source_file="Thing.java",
            line_covered=1,
            line_missed=3,
        )


if __name__ == "__main__":
    unittest.main()
