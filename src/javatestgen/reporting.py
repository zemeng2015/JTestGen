from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from html import escape
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
        html_path = self.root / "report.html"
        self.report.artifacts["report.json"] = str(report_path)
        self.report.artifacts["summary.md"] = str(summary_path)
        self.report.artifacts["report.html"] = str(html_path)
        report_path.write_text(json.dumps(asdict(self.report), indent=2, sort_keys=True), encoding="utf-8")
        summary_path.write_text(format_summary_markdown(self.report), encoding="utf-8")
        html_path.write_text(format_html_report(self.report), encoding="utf-8")


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


def format_html_report(report: RunReport) -> str:
    artifact_items = "\n".join(f"<li><code>{escape(name)}</code></li>" for name in sorted(report.artifacts))
    error_items = "\n".join(f"<li>{escape(error)}</li>" for error in report.errors) or "<li>None</li>"
    prompt_items = "\n".join(
        f"<li>{escape(name)}: <code>{escape(version)}</code></li>"
        for name, version in sorted(report.prompt_versions.items())
    ) or "<li>None recorded</li>"
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>JTestGen Run Report - {escape(report.status)}</title>
    <style>
      body {{ font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 40px; color: #1f2933; line-height: 1.5; }}
      main {{ max-width: 960px; margin: 0 auto; }}
      h1 {{ margin-bottom: 8px; }}
      .meta {{ color: #5f6b7a; margin-bottom: 28px; }}
      .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin: 24px 0; }}
      .card {{ border: 1px solid #d8dee4; border-radius: 8px; padding: 16px; background: #fff; }}
      .label {{ color: #5f6b7a; font-size: 13px; font-weight: 700; text-transform: uppercase; }}
      .value {{ font-size: 24px; font-weight: 800; margin-top: 6px; }}
      table {{ width: 100%; border-collapse: collapse; margin: 16px 0 28px; }}
      th, td {{ border-bottom: 1px solid #d8dee4; padding: 10px; text-align: left; }}
      th {{ background: #f6f8fa; }}
      code {{ background: #f6f8fa; padding: 2px 5px; border-radius: 4px; }}
      .note {{ border-left: 4px solid #0f766e; padding: 12px 16px; background: #f0fdfa; }}
    </style>
  </head>
  <body>
    <main>
      <h1>JTestGen Run Report</h1>
      <p class="meta">Run <code>{escape(report.run_id)}</code> for <code>{escape(report.project)}</code></p>
      <div class="grid">
        <div class="card"><div class="label">Status</div><div class="value">{escape(report.status)}</div></div>
        <div class="card"><div class="label">Target</div><div class="value">{escape(report.target_class or "n/a")}</div></div>
        <div class="card"><div class="label">Repairs</div><div class="value">{report.repair_attempts}</div></div>
        <div class="card"><div class="label">Duration</div><div class="value">{_duration(report.duration_seconds)}</div></div>
      </div>
      <h2>Coverage</h2>
      <table>
        <thead><tr><th>Scope</th><th>Before</th><th>After</th><th>Delta</th></tr></thead>
        <tbody>
          <tr><td>Target class</td><td>{_percent(report.baseline_class_line_coverage)}</td><td>{_percent(report.final_class_line_coverage)}</td><td>{_signed_percent(report.class_line_coverage_delta)}</td></tr>
          <tr><td>Project</td><td>{_percent(report.baseline_project_line_coverage)}</td><td>{_percent(report.final_project_line_coverage)}</td><td>{_signed_percent(report.project_line_coverage_delta)}</td></tr>
        </tbody>
      </table>
      <h2>Validation</h2>
      <ul>
        <li>Verify command: <code>{escape(report.verify_command or "not recorded")}</code></li>
        <li>Test command: <code>{escape(report.test_command or "not recorded")}</code></li>
        <li>Generated test: <code>{escape(report.generated_test_path or "not recorded")}</code></li>
      </ul>
      <h2>Prompt Versions</h2>
      <ul>{prompt_items}</ul>
      <h2>Errors</h2>
      <ul>{error_items}</ul>
      <h2>Artifacts</h2>
      <ul>{artifact_items}</ul>
      <p class="note">Generated tests are reviewable candidates. Maven success and coverage improvement do not prove business correctness.</p>
    </main>
  </body>
</html>
"""


def _percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2%}"


def _signed_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2%}"


def _duration(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}s"
