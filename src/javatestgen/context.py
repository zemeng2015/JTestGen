from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .java_source import JavaClass, discover_java_classes


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
    related_sources: list[SampleTest]
    existing_target_test: SampleTest | None = None
    test_package: str | None = None


def build_prompt_context(
    project: Path,
    target: JavaClass,
    generated_test_path: Path,
    rules_file: Path | None,
    sample_limit: int,
) -> PromptContext:
    test_root = project / "src" / "test" / "java"
    return PromptContext(
        rules=load_rules(project, rules_file),
        sample_tests=find_sample_tests(test_root, target, sample_limit, generated_test_path),
        related_sources=find_related_sources(project / "src" / "main" / "java", target),
        existing_target_test=find_existing_target_test(generated_test_path),
        test_package=infer_test_package(test_root, target, generated_test_path),
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


def find_sample_tests(
    test_root: Path,
    target: JavaClass,
    limit: int,
    generated_test_path: Path | None = None,
) -> list[SampleTest]:
    if limit <= 0 or not test_root.exists():
        return []

    test_files = sorted(
        path
        for path in test_root.glob("**/*.java")
        if path.is_file()
        and (generated_test_path is None or path.resolve() != generated_test_path.resolve())
        and (path.name.endswith("Test.java") or path.name.endswith("Tests.java"))
        and "@Test" in path.read_text(encoding="utf-8")
    )
    package_path = Path(*target.package.split(".")) if target.package else Path()

    def score(path: Path) -> tuple[int, int, str]:
        relative = path.relative_to(test_root)
        same_package = relative.parent == package_path
        similar_name = target.type_name.lower() in path.stem.lower()
        package_distance = _package_distance(target.package, relative.parent)
        return (
            0 if similar_name else 1,
            0 if same_package else package_distance,
            str(relative),
        )

    samples = []
    for path in sorted(test_files, key=score)[:limit]:
        samples.append(SampleTest(path=path, source=path.read_text(encoding="utf-8")))
    return samples


def find_existing_target_test(generated_test_path: Path) -> SampleTest | None:
    if not generated_test_path.exists() or not generated_test_path.is_file():
        return None
    return SampleTest(
        path=generated_test_path,
        source=generated_test_path.read_text(encoding="utf-8"),
    )


def find_related_sources(main_root: Path, target: JavaClass, limit: int = 4) -> list[SampleTest]:
    if limit <= 0 or not main_root.exists():
        return []

    referenced_names = _referenced_type_names(target.source)
    related = []
    for java_class in discover_java_classes(main_root, "**/*.java"):
        if java_class.source_path.resolve() == target.source_path.resolve():
            continue
        if java_class.type_name not in referenced_names:
            continue
        if java_class.package != target.package and f"{java_class.package}.{java_class.type_name}" not in target.source:
            continue
        related.append(
            SampleTest(
                path=java_class.source_path,
                source=java_class.source,
            )
        )
    related.sort(key=lambda item: (0 if item.path.parent == target.source_path.parent else 1, str(item.path)))
    return related[:limit]


def infer_test_package(test_root: Path, target: JavaClass, generated_test_path: Path) -> str:
    if generated_test_path.exists():
        package_name = _read_package(generated_test_path)
        if package_name:
            return package_name

    samples = find_sample_tests(test_root, target, 1, generated_test_path)
    if samples:
        package_name = _read_package(samples[0].path)
        if package_name:
            return package_name
    return target.package


def _read_package(path: Path) -> str | None:
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("package ") and stripped.endswith(";"):
            return stripped.removeprefix("package ").removesuffix(";").strip()
    return None


def _package_distance(target_package: str, test_relative_parent: Path) -> int:
    target_parts = [part for part in target_package.split(".") if part]
    test_parts = [part for part in test_relative_parent.parts if part not in {"test", "tests", "unittest"}]
    common = len(set(target_parts) & set(test_parts))
    same_tail = target_parts[-1:] == test_parts[-1:]
    return (0 if same_tail else 10) + max(len(target_parts), len(test_parts)) - common


def _referenced_type_names(source: str) -> set[str]:
    names = set(re.findall(r"\b[A-Z][A-Za-z0-9_]*\b", source))
    ignored = {
        "Override",
        "SuppressWarnings",
        "Deprecated",
        "FunctionalInterface",
        "SafeVarargs",
    }
    return names - ignored
