from __future__ import annotations

from dataclasses import dataclass

from .coverage import ClassCoverage
from .java_source import JavaClass, find_java_class


@dataclass(frozen=True)
class TargetCandidate:
    java_class: JavaClass
    coverage: ClassCoverage
    skip_reason: str | None = None

    @property
    def selectable(self) -> bool:
        return self.skip_reason is None


def build_target_candidates(classes: list[JavaClass], coverages: list[ClassCoverage]) -> list[TargetCandidate]:
    candidates: list[TargetCandidate] = []
    for coverage in coverages:
        java_class = find_java_class(classes, coverage.qualified_name, coverage.source_file)
        if java_class is None:
            continue
        candidates.append(
            TargetCandidate(
                java_class=java_class,
                coverage=coverage,
                skip_reason=skip_reason(java_class, coverage),
            )
        )
    return candidates


def pick_target_candidate(candidates: list[TargetCandidate]) -> TargetCandidate | None:
    ranked = rank_target_candidates(candidates)
    if not ranked:
        return None
    return ranked[0]


def rank_target_candidates(candidates: list[TargetCandidate], limit: int | None = None) -> list[TargetCandidate]:
    selectable = [
        candidate
        for candidate in candidates
        if candidate.selectable and candidate.coverage.total_lines > 0 and candidate.coverage.line_ratio < 1.0
    ]
    return sorted(
        selectable,
        key=lambda candidate: (
            0 if candidate.coverage.line_covered == 0 else 1,
            candidate.coverage.line_ratio,
            -candidate.coverage.line_missed,
            candidate.coverage.qualified_name,
        ),
    )[:limit]


def skip_reason(java_class: JavaClass, coverage: ClassCoverage) -> str | None:
    source = _strip_comments(java_class.source)
    declaration = _declaration_line(source, java_class.type_name)
    if "$" in coverage.qualified_name:
        return "inner class"
    if java_class.source_path.name in {"module-info.java", "package-info.java"}:
        return "metadata source"
    lowered_path = str(java_class.relative_path).replace("\\", "/").lower()
    if "/generated/" in lowered_path or lowered_path.startswith("generated/"):
        return "generated source"
    if "@Generated" in source or "javax.annotation.Generated" in source or "jakarta.annotation.Generated" in source:
        return "generated annotation"
    if "interface " in declaration or "@interface " in declaration:
        return "interface or annotation"
    if "abstract class " in declaration:
        return "abstract class"
    if java_class.type_name.endswith(("Exception", "Error")) and coverage.total_lines <= 5:
        return "trivial exception type"
    return None


def _declaration_line(source: str, type_name: str) -> str:
    for line in source.splitlines():
        if type_name in line and any(token in line for token in (" class ", " interface ", " enum ", " record ", "@interface ")):
            return line
    return ""


def _strip_comments(source: str) -> str:
    lines = []
    in_block = False
    for line in source.splitlines():
        stripped = line
        if in_block:
            if "*/" in stripped:
                stripped = stripped.split("*/", 1)[1]
                in_block = False
            else:
                continue
        while "/*" in stripped:
            before, after = stripped.split("/*", 1)
            if "*/" in after:
                stripped = before + after.split("*/", 1)[1]
            else:
                stripped = before
                in_block = True
                break
        lines.append(stripped.split("//", 1)[0])
    return "\n".join(lines)
