from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class RunReport:
    run_id: str
    project: str
    status: str = "started"
    target_class: str | None = None
    generated_test_path: str | None = None
    baseline_project_line_coverage: float | None = None
    final_project_line_coverage: float | None = None
    baseline_class_line_coverage: float | None = None
    final_class_line_coverage: float | None = None
    repair_attempts: int = 0
    duration_seconds: float | None = None
    verify_command: str | None = None
    test_command: str | None = None
    project_line_coverage_delta: float | None = None
    class_line_coverage_delta: float | None = None
    prompt_versions: dict[str, str] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


class RunArtifacts:
    def __init__(self, project: Path, enabled: bool = True) -> None:
        self.enabled = enabled
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        self.run_id = f"{timestamp}-{uuid.uuid4().hex[:8]}"
        self.root = project / ".jtestgen" / "runs" / self.run_id
        self.report = RunReport(run_id=self.run_id, project=str(project))
        if self.enabled:
            self.root.mkdir(parents=True, exist_ok=True)

    def write_text(self, name: str, text: str) -> None:
        if not self.enabled:
            return
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        self.report.artifacts[name] = str(path)

    def update(self, **values: Any) -> None:
        for key, value in values.items():
            setattr(self.report, key, value)
        self.flush()

    def add_error(self, error: str) -> None:
        self.report.errors.append(error)
        self.flush()

    def flush(self) -> None:
        if not self.enabled:
            return
        report_path = self.root / "report.json"
        summary_path = self.root / "summary.md"
        self.report.artifacts["report.json"] = str(report_path)
        self.report.artifacts["summary.md"] = str(summary_path)
        report_path.write_text(json.dumps(asdict(self.report), indent=2, sort_keys=True), encoding="utf-8")
        summary_path.write_text(format_summary_markdown(self.report), encoding="utf-8")


def format_summary_markdown(report: RunReport) -> str:
    lines = [
        "# JTestGen Run Summary",
        "",
        f"- Run ID: `{report.run_id}`",
        f"- Status: `{report.status}`",
        f"- Project: `{report.project}`",
    ]
    if report.target_class:
        lines.append(f"- Target class: `{report.target_class}`")
    if report.generated_test_path:
        lines.append(f"- Generated test: `{report.generated_test_path}`")
    if report.duration_seconds is not None:
        lines.append(f"- Duration: `{report.duration_seconds:.3f}s`")
    lines.extend(["", "## Coverage"])
    lines.extend(
        [
            "| Scope | Before | After | Delta |",
            "| --- | ---: | ---: | ---: |",
            (
                "| Target class | "
                f"{_percent(report.baseline_class_line_coverage)} | "
                f"{_percent(report.final_class_line_coverage)} | "
                f"{_signed_percent(report.class_line_coverage_delta)} |"
            ),
            (
                "| Project | "
                f"{_percent(report.baseline_project_line_coverage)} | "
                f"{_percent(report.final_project_line_coverage)} | "
                f"{_signed_percent(report.project_line_coverage_delta)} |"
            ),
        ]
    )
    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"- Repair attempts: `{report.repair_attempts}`",
            f"- Verify command: `{report.verify_command or 'not recorded'}`",
            f"- Test command: `{report.test_command or 'not recorded'}`",
        ]
    )
    if report.prompt_versions:
        lines.extend(["", "## Prompt Versions", ""])
        for name, version in sorted(report.prompt_versions.items()):
            lines.append(f"- {name}: `{version}`")
    if report.errors:
        lines.extend(["", "## Errors", ""])
        for error in report.errors:
            lines.append(f"- {error}")
    lines.extend(["", "## Artifacts", ""])
    for name in sorted(report.artifacts):
        lines.append(f"- `{name}`")
    lines.extend(
        [
            "",
            "## Review Note",
            "",
            "Generated tests are reviewable candidates. Maven success and coverage improvement do not prove business correctness.",
            "",
        ]
    )
    return "\n".join(lines)


def _percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2%}"


def _signed_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2%}"
