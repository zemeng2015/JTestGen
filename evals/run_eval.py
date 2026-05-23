from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"


EVALS = [
    {
        "name": "tiny-success",
        "fixture": "tiny-maven-project",
        "responses": "tiny-maven-project-responses.json",
        "expected_status": "success",
        "expected_repair_attempts": 0,
    },
    {
        "name": "tiny-repair-needed",
        "fixture": "tiny-maven-project",
        "responses": "tiny-maven-project-repair-responses.json",
        "expected_status": "success",
        "expected_repair_attempts": 1,
    },
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic JTestGen eval fixtures.")
    parser.add_argument("--maven-command", default="mvn", help="Maven command to use.")
    args = parser.parse_args()

    sys.path.insert(0, str(SRC))
    from javatestgen.config import RunConfig
    from javatestgen.generator import FileGenerator
    from javatestgen.runner import MavenRunner
    from javatestgen.workflow import TestGenerationWorkflow

    results = []
    failures = 0
    for eval_case in EVALS:
        result = run_case(args.maven_command, eval_case)
        results.append(result)
        if (
            result["exit_code"] != 0
            or result["status"] != eval_case["expected_status"]
            or result["repair_attempts"] != eval_case["expected_repair_attempts"]
        ):
            failures += 1

    print(json.dumps({"failures": failures, "results": results}, indent=2, sort_keys=True))
    return 1 if failures else 0


def run_case(maven_command: str, eval_case: dict[str, object]) -> dict[str, object]:
    from javatestgen.config import RunConfig
    from javatestgen.generator import FileGenerator
    from javatestgen.runner import MavenRunner
    from javatestgen.workflow import TestGenerationWorkflow

    fixture = REPO_ROOT / "evals" / "fixtures" / str(eval_case["fixture"])
    responses = REPO_ROOT / "evals" / "fixtures" / str(eval_case["responses"])
    with tempfile.TemporaryDirectory() as temp_dir:
        project = Path(temp_dir) / str(eval_case["fixture"])
        shutil.copytree(fixture, project)
        config = RunConfig(
            project=project,
            target_coverage=0.50,
            target_class="com.example.Calculator",
            test_suffix="GeneratedTest",
            maven_command=maven_command,
        )
        workflow = TestGenerationWorkflow(
            config=config,
            generator=FileGenerator.from_file(responses),
            runner=MavenRunner(project, maven_command=maven_command),
        )
        exit_code = workflow.run()
        report_path = max((project / ".jtestgen" / "runs").glob("*/report.json"))
        report = json.loads(report_path.read_text(encoding="utf-8"))
        return {
            "name": eval_case["name"],
            "exit_code": exit_code,
            "status": report["status"],
            "target_class": report["target_class"],
            "baseline_class_line_coverage": report["baseline_class_line_coverage"],
            "final_class_line_coverage": report["final_class_line_coverage"],
            "repair_attempts": report["repair_attempts"],
        }


if __name__ == "__main__":
    raise SystemExit(main())
