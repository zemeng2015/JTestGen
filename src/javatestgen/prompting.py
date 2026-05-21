from __future__ import annotations

from .context import PromptContext
from .coverage import ClassCoverage
from .generator import GenerationRequest
from .java_source import JavaClass


SYSTEM_PROMPT = """You generate production-quality Java unit tests.
Return only a complete Java source file, with no Markdown fences.
Prefer JUnit 5 and Mockito only when mocking is necessary.
Keep tests deterministic, readable, and focused on public behavior.
Do not change production code.
"""


def build_initial_request(
    java_class: JavaClass,
    test_class_name: str,
    coverage: ClassCoverage,
    context: PromptContext,
) -> GenerationRequest:
    user_prompt = f"""Create a Java unit test file for the least-covered production class from the JaCoCo report.

Requirements:
- Test class name: {test_class_name}
- Production class qualified name: {java_class.qualified_name}
- Current class line coverage: {coverage.line_ratio:.2%} ({coverage.line_covered} covered, {coverage.line_missed} missed)
- Use the same package as the production class unless imports are better.
- Cover normal behavior, edge cases, and exception paths visible from the source.
- Prefer tests that increase coverage for this exact class.
- Follow the project rules and the style of the sample tests.
- Return only compilable Java code.

Project test generation rules:
```text
{context.rules}
```

Production source:
```java
{java_class.source}
```

Existing sample tests:
{format_sample_tests(context)}
"""
    return GenerationRequest(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)


def build_repair_request(
    java_class: JavaClass,
    current_test_source: str,
    maven_output: str,
    test_class_name: str,
    coverage: ClassCoverage,
    context: PromptContext,
) -> GenerationRequest:
    user_prompt = f"""Repair this generated Java unit test so this exact Maven command passes:
mvn -q -Dtest={test_class_name} test

Requirements:
- Test class name: {test_class_name}
- Production class qualified name: {java_class.qualified_name}
- Original class line coverage before generation: {coverage.line_ratio:.2%} ({coverage.line_covered} covered, {coverage.line_missed} missed)
- Preserve useful coverage while fixing compilation or test failures.
- Diagnose the Maven output first: distinguish compile errors, missing dependencies, assertion failures, Mockito issues, and checked exceptions.
- Do not invent new dependencies. Use only APIs and libraries already implied by the source or sample tests.
- If behavior is uncertain, assert stable public contracts rather than private implementation details.
- Keep the same package and class name unless the Maven output proves they are wrong.
- Follow the project rules and sample test style.
- Return only the complete corrected Java source file.

Project test generation rules:
```text
{context.rules}
```

Production source:
```java
{java_class.source}
```

Current generated test:
```java
{current_test_source}
```

Maven output:
```text
{maven_output[-12000:]}
```

Existing sample tests:
{format_sample_tests(context)}
"""
    return GenerationRequest(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)


def format_sample_tests(context: PromptContext) -> str:
    if not context.sample_tests:
        return "No sample tests were found."

    blocks = []
    for sample in context.sample_tests:
        blocks.append(
            f"Path: {sample.path}\n"
            "```java\n"
            f"{sample.source[-8000:]}\n"
            "```"
        )
    return "\n\n".join(blocks)
