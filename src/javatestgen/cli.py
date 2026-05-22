from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import RunConfig
from .generator import OpenAICompatibleGenerator
from .runner import MavenRunner
from .workflow import TestGenerationWorkflow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="java-testgen",
        description="Generate Java unit tests, run JaCoCo coverage, and repair failing generated tests.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

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


if __name__ == "__main__":
    sys.exit(main())
