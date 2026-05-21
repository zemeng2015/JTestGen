from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .java_source import JavaClass


DEFAULT_RULES = """Generated test rules:
- Follow the existing project's unit test style, naming, imports, assertions, and mocking approach.
- Prefer focused unit tests over broad integration tests unless the sample tests clearly use integration style.
- Do not modify production code.
- Do not add sleeps, network calls, filesystem writes outside temporary directories, or time-dependent assertions.
- Do not invent dependencies that are not already visible in the project or sample tests.
- Keep tests deterministic and independent from execution order.
"""


@dataclass(frozen=True)
class SampleTest:
    path: Path
    source: str


@dataclass(frozen=True)
class PromptContext:
    rules: str
    sample_tests: list[SampleTest]


def build_prompt_context(project: Path, target: JavaClass, rules_file: Path | None, sample_limit: int) -> PromptContext:
    return PromptContext(
        rules=load_rules(project, rules_file),
        sample_tests=find_sample_tests(project / "src" / "test" / "java", target, sample_limit),
    )


def load_rules(project: Path, explicit_rules_file: Path | None) -> str:
    candidates = []
    if explicit_rules_file:
        candidates.append(explicit_rules_file)
    candidates.extend(
        [
            project / "TESTGEN_RULES.md",
            project / ".testgen-rules.md",
            project / "testgen-rules.md",
        ]
    )
    for path in candidates:
        if path.exists() and path.is_file():
            return path.read_text(encoding="utf-8")
    return DEFAULT_RULES


def find_sample_tests(test_root: Path, target: JavaClass, limit: int) -> list[SampleTest]:
    if limit <= 0 or not test_root.exists():
        return []

    test_files = sorted(
        path
        for path in test_root.glob("**/*.java")
        if path.is_file() and (path.name.endswith("Test.java") or path.name.endswith("Tests.java"))
    )
    package_path = Path(*target.package.split(".")) if target.package else Path()

    def score(path: Path) -> tuple[int, int, str]:
        relative = path.relative_to(test_root)
        same_package = relative.parent == package_path
        similar_name = target.type_name.lower() in path.stem.lower()
        return (
            0 if similar_name else 1,
            0 if same_package else len(relative.parts),
            str(relative),
        )

    samples = []
    for path in sorted(test_files, key=score)[:limit]:
        samples.append(SampleTest(path=path, source=path.read_text(encoding="utf-8")))
    return samples
