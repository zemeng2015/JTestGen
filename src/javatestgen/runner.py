from __future__ import annotations

import subprocess
import os
import shutil
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
    def __init__(
        self,
        project: Path,
        maven_command: str | None = None,
        verify_args: tuple[str, ...] = (),
    ) -> None:
        self.project = project
        self.maven_command = resolve_maven_command(maven_command)
        self.verify_args = list(verify_args)

    def verify(self) -> CommandResult:
        return self._run([self.maven_command, "-q", *self.verify_args, "verify"])

    def test_generated_class(self, test_class_name: str) -> CommandResult:
        return self._run([self.maven_command, "-q", *self.verify_args, f"-Dtest={test_class_name}", "test"])

    def test_generated_class_command(self, test_class_name: str) -> str:
        return " ".join([self.maven_command, "-q", *self.verify_args, f"-Dtest={test_class_name}", "test"])

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


def resolve_maven_command(maven_command: str | None = None) -> str:
    candidates = [
        maven_command,
        os.getenv("JTESTGEN_MAVEN_CMD"),
        "mvn",
        "mvn.cmd",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
        if Path(candidate).exists():
            return candidate
    return maven_command or os.getenv("JTESTGEN_MAVEN_CMD") or "mvn"
