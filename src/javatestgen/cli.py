from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

from .config import RunConfig
from .coverage import parse_class_coverages
from .generator import OpenAICompatibleGenerator
from .java_source import discover_java_classes
from .runner import MavenRunner
from .targeting import build_target_candidates, rank_target_candidates
from .workflow import TestGenerationWorkflow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="java-testgen",
        description="Generate Java unit tests, run JaCoCo coverage, and repair failing generated tests.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Check whether a project looks ready for JTestGen.")
    doctor.add_argument("project", type=Path, help="Path to the target Maven Java project.")
    doctor.add_argument("--maven-command", default=None, help="Maven executable to use, for example mvn.cmd or C:\\path\\to\\mvn.cmd.")

    scan = subparsers.add_parser("scan", help="List low-coverage target candidates without calling an LLM.")
    scan.add_argument("project", type=Path, help="Path to the target Maven Java project.")
    scan.add_argument("--class-glob", default="**/*.java", help="Glob under src/main/java.")
    scan.add_argument("--top", type=int, default=10, help="Number of target candidates to print.")
    scan.add_argument("--maven-command", default=None, help="Maven executable to use, for example mvn.cmd or C:\\path\\to\\mvn.cmd.")
    scan.add_argument(
        "--verify-arg",
        action="append",
        default=[],
        help="Extra Maven argument for baseline verify. Repeat as needed, for example --verify-arg=-DskipITs.",
    )
    scan.add_argument("--skip-verify", action="store_true", help="Use an existing JaCoCo XML report instead of running Maven verify.")

    run = subparsers.add_parser("run", help="Run generation, coverage, and repair loop.")
    run.add_argument("project", type=Path, help="Path to the target Maven Java project.")
    run.add_argument("--class-glob", default="**/*.java", help="Glob under src/main/java.")
    run.add_argument("--target-coverage", type=float, default=0.80, help="Required line coverage ratio.")
    run.add_argument("--max-repairs", type=int, default=3, help="Repair attempts per generated test.")
    run.add_argument("--sample-tests", type=int, default=3, help="Existing test files to include as style examples.")
    run.add_argument(
        "--target-class",
        default=None,
        help="Optional fully qualified or simple class name to generate tests for instead of auto-selecting.",
    )
    run.add_argument("--test-suffix", default="Test", help="Generated test class suffix.")
    run.add_argument("--rules-file", type=Path, default=None, help="Optional project-specific rules for generated tests.")
    run.add_argument("--maven-command", default=None, help="Maven executable to use, for example mvn.cmd or C:\\path\\to\\mvn.cmd.")
    run.add_argument(
        "--verify-arg",
        action="append",
        default=[],
        help="Extra Maven argument for baseline/final verify. Repeat as needed, for example --verify-arg=-DskipITs.",
    )
    run.add_argument("--model", default=None, help="Override OPENAI_MODEL.")
    run.add_argument("--no-artifacts", action="store_true", help="Do not write .jtestgen run artifacts.")
    run.add_argument("--dry-run", action="store_true", help="Print prompts without writing or running tests.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        return run_doctor(args.project.resolve(), args.maven_command)
    if args.command == "scan":
        return run_scan(args)
    if args.command != "run":
        raise AssertionError(f"Unhandled command: {args.command}")

    config = RunConfig(
        project=args.project.resolve(),
        class_glob=args.class_glob,
        target_coverage=args.target_coverage,
        max_repairs=args.max_repairs,
        sample_tests=args.sample_tests,
        target_class=args.target_class,
        test_suffix=args.test_suffix,
        rules_file=args.rules_file.resolve() if args.rules_file else None,
        maven_command=args.maven_command,
        verify_args=tuple(args.verify_arg),
        save_artifacts=not args.no_artifacts,
        model=args.model,
        dry_run=args.dry_run,
    )

    workflow = TestGenerationWorkflow(
        config=config,
        generator=OpenAICompatibleGenerator(model_override=config.model),
        runner=MavenRunner(
            config.project,
            maven_command=config.maven_command,
            verify_args=config.verify_args,
        ),
    )
    return workflow.run()


def run_doctor(project: Path, maven_command: str | None = None) -> int:
    checks: list[tuple[str, str, str]] = []
    maven = _resolve_for_check(maven_command)
    checks.append(_check("Project directory", project.exists(), str(project)))
    checks.append(_check("pom.xml", (project / "pom.xml").exists(), str(project / "pom.xml")))
    checks.append(_check("src/main/java", (project / "src" / "main" / "java").exists(), str(project / "src" / "main" / "java")))
    checks.append(_check("src/test/java", (project / "src" / "test" / "java").exists(), str(project / "src" / "test" / "java"), required=False))
    checks.append(_check("Maven executable", maven is not None, maven or (maven_command or "mvn"), required=True))
    checks.append(
        _check(
            "JaCoCo XML",
            (project / "target" / "site" / "jacoco" / "jacoco.xml").exists(),
            str(project / "target" / "site" / "jacoco" / "jacoco.xml"),
            required=False,
        )
    )
    checks.append(_check("OPENAI_API_KEY", bool(os.getenv("OPENAI_API_KEY")), "set in environment", required=False))
    for status, name, detail in checks:
        print(f"{status:>6}  {name}: {detail}")
    required_failed = any(status == "FAIL" for status, _, _ in checks)
    if required_failed:
        print("Doctor result: project is not ready for JTestGen run.")
        return 1
    print("Doctor result: required checks passed. Warnings may still need attention before generation.")
    return 0


def run_scan(args: argparse.Namespace) -> int:
    config = RunConfig(
        project=args.project.resolve(),
        class_glob=args.class_glob,
        maven_command=args.maven_command,
        verify_args=tuple(args.verify_arg),
    )
    if not (config.project / "pom.xml").exists():
        print(f"Expected a Maven pom.xml in: {config.project}")
        return 1
    runner = MavenRunner(config.project, maven_command=config.maven_command, verify_args=config.verify_args)
    if not args.skip_verify:
        print(f"Running baseline coverage: {runner.verify_command()}")
        result = runner.verify()
        if not result.ok:
            print("Baseline mvn verify failed. Fix the target project or pass --skip-verify with an existing JaCoCo XML.")
            print(result.output[-4000:])
            return 1
    if not config.jacoco_xml.exists():
        print(f"JaCoCo XML not found: {config.jacoco_xml}")
        print("Run Maven with JaCoCo enabled, or configure the project so target/site/jacoco/jacoco.xml is produced.")
        return 1
    classes = discover_java_classes(config.main_source_root, config.class_glob)
    coverages = parse_class_coverages(config.jacoco_xml)
    ranked = rank_target_candidates(build_target_candidates(classes, coverages), limit=args.top)
    if not ranked:
        print("No selectable low-coverage candidates found.")
        return 1
    print("Top coverage targets")
    print("| Rank | Class | Coverage | Missed Lines | Covered Lines |")
    print("| ---: | --- | ---: | ---: | ---: |")
    for index, candidate in enumerate(ranked, start=1):
        coverage = candidate.coverage
        print(
            f"| {index} | `{candidate.java_class.qualified_name}` | "
            f"{coverage.line_ratio:.2%} | {coverage.line_missed} | {coverage.line_covered} |"
        )
    return 0


def _check(name: str, ok: bool, detail: str, required: bool = True) -> tuple[str, str, str]:
    if ok:
        return "OK", name, detail
    return ("FAIL" if required else "WARN", name, detail)


def _resolve_for_check(maven_command: str | None = None) -> str | None:
    candidates = [maven_command, os.getenv("JTESTGEN_MAVEN_CMD"), "mvn", "mvn.cmd"]
    for candidate in candidates:
        if not candidate:
            continue
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
        if Path(candidate).exists():
            return candidate
    return None


if __name__ == "__main__":
    sys.exit(main())
