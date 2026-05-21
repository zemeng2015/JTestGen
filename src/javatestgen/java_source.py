from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


PACKAGE_RE = re.compile(r"^\s*package\s+([\w.]+)\s*;", re.MULTILINE)
PUBLIC_TYPE_RE = re.compile(r"\bpublic\s+(?:final\s+|abstract\s+)?(?:class|interface|enum|record)\s+(\w+)")
ANY_TYPE_RE = re.compile(r"\b(?:class|interface|enum|record)\s+(\w+)")


@dataclass(frozen=True)
class JavaClass:
    source_path: Path
    relative_path: Path
    source: str
    package: str
    type_name: str

    def test_relative_path(self, suffix: str) -> Path:
        package_path = Path(*self.package.split(".")) if self.package else Path()
        return package_path / f"{self.type_name}{suffix}.java"

    @property
    def qualified_name(self) -> str:
        return f"{self.package}.{self.type_name}" if self.package else self.type_name


def discover_java_classes(source_root: Path, class_glob: str) -> list[JavaClass]:
    if not source_root.exists():
        raise FileNotFoundError(f"Main source root does not exist: {source_root}")

    classes: list[JavaClass] = []
    for path in sorted(source_root.glob(class_glob)):
        if not path.is_file() or path.name.endswith("Test.java"):
            continue
        source = path.read_text(encoding="utf-8")
        package = _match(PACKAGE_RE, source) or ""
        type_name = _match(PUBLIC_TYPE_RE, source) or _match(ANY_TYPE_RE, source)
        if not type_name:
            continue
        classes.append(
            JavaClass(
                source_path=path,
                relative_path=path.relative_to(source_root),
                source=source,
                package=package,
                type_name=type_name,
            )
        )
    return classes


def find_java_class(classes: list[JavaClass], qualified_name: str, source_file: str) -> JavaClass | None:
    top_level_name = qualified_name.split(".")[-1]
    if "$" in top_level_name:
        top_level_name = top_level_name.split("$", 1)[0]

    for java_class in classes:
        if java_class.qualified_name == qualified_name:
            return java_class

    for java_class in classes:
        if java_class.source_path.name == source_file and java_class.type_name == top_level_name:
            return java_class

    for java_class in classes:
        if java_class.source_path.name == source_file:
            return java_class
    return None


def _match(pattern: re.Pattern[str], text: str) -> str | None:
    found = pattern.search(text)
    return found.group(1) if found else None
