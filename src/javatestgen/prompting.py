from __future__ import annotations

from .context import PromptContext
from .coverage import ClassCoverage
from .generator import GenerationRequest
from .java_source import JavaClass


GENERATION_PROMPT_VERSION = "generation-v3"
REPAIR_PROMPT_VERSION = "repair-v3"


SYSTEM_PROMPT = """You generate production-quality Java unit tests.
Return only a complete Java source file, with no Markdown fences.
Prefer JUnit 5 and Mockito only when mocking is necessary.
Keep tests deterministic, readable, and focused on public behavior.
Do not change production code.
Do not invent project dependencies, build plugins, source files, or helper APIs.
"""


def build_initial_request(
    java_class: JavaClass,
    test_class_name: str,
    test_path: str,
    coverage: ClassCoverage,
    context: PromptContext,
) -> GenerationRequest:
    test_package = context.test_package or java_class.package
    user_prompt = f"""Task: create one Java unit test file for a production class selected from a JaCoCo coverage report.

Target:
- Test class name: {test_class_name}
- Generated test path: {test_path}
- Production class qualified name: {java_class.qualified_name}
- Current class line coverage: {coverage.line_ratio:.2%} ({coverage.line_covered} covered, {coverage.line_missed} missed)

Output contract:
- Return exactly one complete Java source file.
- Use package `{test_package}`.
- The public/top-level test class must be named `{test_class_name}`.
- Do not include Markdown fences, explanations, diffs, or multiple alternatives.
- Do not modify or duplicate existing tests. Add focused tests that complement them.

Coverage strategy:
- Prefer tests that execute currently uncovered public behavior of `{java_class.type_name}`.
- Exercise edge cases and exception paths only when they are stable and visible from the source.
- Avoid brittle assertions on logging text, timing, object identity, private implementation details, or platform-specific paths unless the existing tests already do this.
- If the class is a tiny adapter/wrapper, verify delegation with a minimal fake/stub instead of adding broad integration tests.

Dependency and style constraints:
- Follow the project rules and the style of the sample tests.
- Use only libraries already visible in the sample tests, imports, or production source.
- Prefer simple hand-written fakes over Mockito unless sample tests clearly use Mockito.

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

Existing generated target test, if any:
{format_existing_target_test(context)}
"""
    return GenerationRequest(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)


def build_repair_request(
    java_class: JavaClass,
    current_test_source: str,
    maven_output: str,
    test_class_name: str,
    test_path: str,
    test_command: str,
    coverage: ClassCoverage,
    context: PromptContext,
) -> GenerationRequest:
    test_package = context.test_package or java_class.package
    user_prompt = f"""Task: repair one generated Java unit test file so this exact Maven command passes:
{test_command}

Target:
- Test class name: {test_class_name}
- Generated test path: {test_path}
- Production class qualified name: {java_class.qualified_name}
- Original class line coverage before generation: {coverage.line_ratio:.2%} ({coverage.line_covered} covered, {coverage.line_missed} missed)

Repair strategy:
- First infer the failure category from Maven output: Java compilation error, missing import/dependency, test discovery/class-name issue, checked exception, assertion failure, Mockito/mocking issue, or runtime exception.
- Make the smallest source change that addresses the failure while preserving coverage intent.
- If an assertion is brittle or behavior is uncertain, replace it with a stable public-contract assertion.
- Do not add sleeps, network calls, dependency changes, build changes, or production-code changes.
- Do not invent dependencies. Use only APIs and libraries already implied by the source or sample tests.
- Keep package `{test_package}` and class name `{test_class_name}` unless the Maven output proves they are wrong.
- If Maven says the package exists in another module, move the test to the sample-test package `{test_package}` and import the production class.
- Follow the project rules and sample test style.

Output contract:
- Return exactly one complete corrected Java source file.
- Do not include Markdown fences, explanations, diffs, or multiple alternatives.

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


def format_existing_target_test(context: PromptContext) -> str:
    if context.existing_target_test is None:
        return "No existing generated target test was found."
    sample = context.existing_target_test
    return (
        f"Path: {sample.path}\n"
        "```java\n"
        f"{sample.source[-8000:]}\n"
        "```"
    )
