from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    output: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class MavenRunner:
    def __init__(self, project: Path) -> None:
        self.project = project

    def verify(self) -> CommandResult:
        return self._run(["mvn", "-q", "verify"])

    def test_generated_class(self, test_class_name: str) -> CommandResult:
        return self._run(["mvn", "-q", f"-Dtest={test_class_name}", "test"])

    def _run(self, command: list[str]) -> CommandResult:
        completed = subprocess.run(
            command,
            cwd=self.project,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        return CommandResult(returncode=completed.returncode, output=completed.stdout)
