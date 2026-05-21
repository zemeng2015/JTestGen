from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CoverageSummary:
    line_covered: int
    line_missed: int

    @property
    def line_ratio(self) -> float:
        total = self.line_covered + self.line_missed
        return 1.0 if total == 0 else self.line_covered / total


@dataclass(frozen=True)
class ClassCoverage:
    qualified_name: str
    package: str
    source_file: str
    line_covered: int
    line_missed: int

    @property
    def line_ratio(self) -> float:
        total = self.line_covered + self.line_missed
        return 1.0 if total == 0 else self.line_covered / total

    @property
    def total_lines(self) -> int:
        return self.line_covered + self.line_missed


def parse_jacoco_xml(path: Path) -> CoverageSummary:
    if not path.exists():
        return CoverageSummary(line_covered=0, line_missed=0)

    root = ET.parse(path).getroot()
    root_counter = root.find("counter[@type='LINE']")
    if root_counter is not None:
        return CoverageSummary(
            line_covered=int(root_counter.attrib.get("covered", "0")),
            line_missed=int(root_counter.attrib.get("missed", "0")),
        )

    class_coverages = parse_class_coverages(path)
    covered = sum(coverage.line_covered for coverage in class_coverages)
    missed = sum(coverage.line_missed for coverage in class_coverages)
    return CoverageSummary(line_covered=covered, line_missed=missed)


def parse_class_coverages(path: Path) -> list[ClassCoverage]:
    if not path.exists():
        return []

    root = ET.parse(path).getroot()
    coverages: list[ClassCoverage] = []
    for package in root.findall("package"):
        package_name = package.attrib.get("name", "").replace("/", ".")
        for class_node in package.findall("class"):
            line_counter = class_node.find("counter[@type='LINE']")
            if line_counter is None:
                continue
            class_name = class_node.attrib.get("name", "").replace("/", ".")
            qualified_name = class_name.replace("$", ".")
            coverages.append(
                ClassCoverage(
                    qualified_name=qualified_name,
                    package=package_name,
                    source_file=class_node.attrib.get("sourcefilename", ""),
                    line_covered=int(line_counter.attrib.get("covered", "0")),
                    line_missed=int(line_counter.attrib.get("missed", "0")),
                )
            )
    return coverages


def pick_lowest_coverage_class(coverages: list[ClassCoverage]) -> ClassCoverage | None:
    candidates = [coverage for coverage in coverages if coverage.total_lines > 0]
    if not candidates:
        return None
    return sorted(
        candidates,
        key=lambda coverage: (
            0 if coverage.line_covered == 0 else 1,
            coverage.line_ratio,
            -coverage.line_missed,
            coverage.qualified_name,
        ),
    )[0]
