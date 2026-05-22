from __future__ import annotations

import json
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
    prompt_versions: dict[str, str] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


class RunArtifacts:
    def __init__(self, project: Path, enabled: bool = True) -> None:
        self.enabled = enabled
        self.run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
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
        path = self.root / "report.json"
        path.write_text(json.dumps(asdict(self.report), indent=2, sort_keys=True), encoding="utf-8")
        self.report.artifacts["report.json"] = str(path)
