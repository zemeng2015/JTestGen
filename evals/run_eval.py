from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic JTestGen eval fixtures.")
    parser.add_argument("--maven-command", default="mvn", help="Maven command to use.")
    args = parser.parse_args()

    sys.path.insert(0, str(SRC))
    from javatestgen.config import RunConfig
    from javatestgen.generator import FileGenerator
    from javatestgen.runner import MavenRunner
    from javatestgen.workflow import TestGenerationWorkflow

    fixture = REPO_ROOT / "evals" / "fixtures" / "tiny-maven-project"
    responses = REPO_ROOT / "evals" / "fixtures" / "tiny-maven-project-responses.json"
    with tempfile.TemporaryDirectory() as temp_dir:
        project = Path(temp_dir) / "tiny-maven-project"
        shutil.copytree(fixture, project)
        config = RunConfig(
            project=project,
            target_coverage=0.50,
            target_class="com.example.Calculator",
            test_suffix="GeneratedTest",
            maven_command=args.maven_command,
        )
        workflow = TestGenerationWorkflow(
            config=config,
            generator=FileGenerator.from_file(responses),
            runner=MavenRunner(project, maven_command=args.maven_command),
        )
        exit_code = workflow.run()
        report_path = max((project / ".jtestgen" / "runs").glob("*/report.json"))
        report = json.loads(report_path.read_text(encoding="utf-8"))
        print(json.dumps({
            "exit_code": exit_code,
            "status": report["status"],
            "target_class": report["target_class"],
            "baseline_class_line_coverage": report["baseline_class_line_coverage"],
            "final_class_line_coverage": report["final_class_line_coverage"],
            "repair_attempts": report["repair_attempts"],
        }, indent=2, sort_keys=True))
        return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
