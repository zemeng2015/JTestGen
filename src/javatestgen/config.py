from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunConfig:
    project: Path
    class_glob: str = "**/*.java"
    target_coverage: float = 0.80
    max_repairs: int = 3
    sample_tests: int = 3
    target_class: str | None = None
    test_suffix: str = "Test"
    rules_file: Path | None = None
    maven_command: str | None = None
    verify_args: tuple[str, ...] = ()
    save_artifacts: bool = True
    model: str | None = None
    dry_run: bool = False
    max_targets: int = 1
    patch_output: Path | None = None

    @property
    def main_source_root(self) -> Path:
        return self.project / "src" / "main" / "java"

    @property
    def test_source_root(self) -> Path:
        return self.project / "src" / "test" / "java"

    @property
    def jacoco_xml(self) -> Path:
        return self.project / "target" / "site" / "jacoco" / "jacoco.xml"
