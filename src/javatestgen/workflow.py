from __future__ import annotations

import re
from pathlib import Path

from .config import RunConfig
from .context import build_prompt_context
from .coverage import ClassCoverage, parse_class_coverages, parse_jacoco_xml, pick_lowest_coverage_class
from .generator import GenerationError, OpenAICompatibleGenerator
from .java_source import JavaClass, discover_java_classes, find_java_class, find_java_class_by_name
from .prompting import build_initial_request, build_repair_request
from .runner import MavenRunner


class TestGenerationWorkflow:
    def __init__(
        self,
        config: RunConfig,
        generator: OpenAICompatibleGenerator,
        runner: MavenRunner,
    ) -> None:
        self.config = config
        self.generator = generator
        self.runner = runner

    def run(self) -> int:
        _validate_project(self.config.project)
        classes = discover_java_classes(self.config.main_source_root, self.config.class_glob)
        if not classes:
            print(f"No Java classes found under {self.config.main_source_root}")
            return 1

        print("Running baseline coverage: mvn -q verify")
        baseline_result = self.runner.verify()
        if not baseline_result.ok:
            print("Baseline mvn verify failed. Fix the target project before generating new tests.")
            print(baseline_result.output[-4000:])
            return 1

        baseline_summary = parse_jacoco_xml(self.config.jacoco_xml)
        baseline_coverages = parse_class_coverages(self.config.jacoco_xml)
        selected = self._select_target_class(classes, baseline_coverages)
        if selected is None:
            print(f"No coverable class found in {self.config.jacoco_xml}")
            return 1

        java_class, class_coverage = selected
        print(
            "Selected target: "
            f"{java_class.qualified_name} with {class_coverage.line_ratio:.2%} line coverage "
            f"({class_coverage.line_covered} covered, {class_coverage.line_missed} missed)"
        )

        ok = self._process_class(java_class, class_coverage)

        print("Running final coverage: mvn -q verify")
        final_result = self.runner.verify()
        if not final_result.ok:
            print("Final mvn verify failed after generation.")
            print(final_result.output[-4000:])
            return 1

        final_summary = parse_jacoco_xml(self.config.jacoco_xml)
        final_class_coverage = self._find_class_coverage(java_class, parse_class_coverages(self.config.jacoco_xml))
        print_generation_report(
            java_class=java_class,
            before=class_coverage,
            after=final_class_coverage,
            baseline_total=baseline_summary.line_ratio,
            final_total=final_summary.line_ratio,
        )

        if final_summary.line_ratio < self.config.target_coverage:
            print(
                f"Coverage below target: {final_summary.line_ratio:.2%} < "
                f"{self.config.target_coverage:.2%}"
            )
            return 1
        return 0 if ok else 1

    def _select_target_class(
        self,
        classes: list[JavaClass],
        coverages: list[ClassCoverage],
    ) -> tuple[JavaClass, ClassCoverage] | None:
        if self.config.target_class:
            java_class = find_java_class_by_name(classes, self.config.target_class)
            if java_class is None:
                raise ValueError(f"--target-class was not found under {self.config.main_source_root}: {self.config.target_class}")
            return java_class, self._find_class_coverage(java_class, coverages)

        remaining = coverages[:]
        while remaining:
            coverage = pick_lowest_coverage_class(remaining)
            if coverage is None:
                return None
            java_class = find_java_class(classes, coverage.qualified_name, coverage.source_file)
            if java_class:
                return java_class, coverage
            remaining = [item for item in remaining if item != coverage]
        return None

    def _find_class_coverage(
        self,
        java_class: JavaClass,
        coverages: list[ClassCoverage],
    ) -> ClassCoverage:
        for coverage in coverages:
            if find_java_class([java_class], coverage.qualified_name, coverage.source_file):
                return coverage
        return ClassCoverage(
            qualified_name=java_class.qualified_name,
            package=java_class.package,
            source_file=java_class.source_path.name,
            line_covered=0,
            line_missed=0,
        )

    def _process_class(self, java_class: JavaClass, coverage: ClassCoverage) -> bool:
        test_class_name = f"{java_class.type_name}{self.config.test_suffix}"
        provisional_test_path = self.config.test_source_root / java_class.test_relative_path(self.config.test_suffix)
        context = build_prompt_context(
            project=self.config.project,
            target=java_class,
            generated_test_path=provisional_test_path,
            rules_file=self.config.rules_file,
            sample_limit=self.config.sample_tests,
        )
        test_path = self.config.test_source_root / java_class.test_relative_path_for_package(
            self.config.test_suffix,
            context.test_package,
        )
        relative_test_path = str(test_path.relative_to(self.config.project))
        request = build_initial_request(
            java_class=java_class,
            test_class_name=test_class_name,
            test_path=relative_test_path,
            coverage=coverage,
            context=context,
        )

        print(f"Generating {test_path.relative_to(self.config.project)} for {java_class.qualified_name}")
        if self.config.dry_run:
            print(request.user_prompt)
            return True

        try:
            generated = clean_java_source(self.generator.generate(request))
        except GenerationError as exc:
            print(exc)
            return False

        write_test(test_path, generated)

        for attempt in range(self.config.max_repairs + 1):
            result = self.runner.test_generated_class(test_class_name)
            if result.ok:
                print(f"Generated test passed: mvn -q -Dtest={test_class_name} test")
                return True

            if attempt >= self.config.max_repairs:
                print(f"Repair limit reached for {test_class_name}")
                print(result.output[-4000:])
                return False

            print(f"Repairing {test_class_name}, attempt {attempt + 1}/{self.config.max_repairs}")
            current_test = test_path.read_text(encoding="utf-8")
            repair_request = build_repair_request(
                java_class=java_class,
                current_test_source=current_test,
                maven_output=result.output,
                test_class_name=test_class_name,
                test_path=relative_test_path,
                test_command=self.runner.test_generated_class_command(test_class_name),
                coverage=coverage,
                context=context,
            )
            try:
                repaired = clean_java_source(self.generator.generate(repair_request))
            except GenerationError as exc:
                print(exc)
                return False
            write_test(test_path, repaired)
        return False


def write_test(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.rstrip() + "\n", encoding="utf-8")


def clean_java_source(source: str) -> str:
    cleaned = source.strip()
    fence = re.fullmatch(r"```(?:java)?\s*(.*?)```", cleaned, flags=re.DOTALL)
    return fence.group(1).strip() if fence else cleaned


def _validate_project(project: Path) -> None:
    if not project.exists():
        raise FileNotFoundError(f"Project does not exist: {project}")
    if not (project / "pom.xml").exists():
        raise FileNotFoundError(f"Expected a Maven pom.xml in: {project}")


def print_generation_report(
    java_class: JavaClass,
    before: ClassCoverage,
    after: ClassCoverage,
    baseline_total: float,
    final_total: float,
) -> None:
    print("Generation report")
    print(f"- Target class: {java_class.qualified_name}")
    print(f"- Class line coverage: {before.line_ratio:.2%} -> {after.line_ratio:.2%}")
    print(f"- Class covered lines: {before.line_covered}/{before.total_lines} -> {after.line_covered}/{after.total_lines}")
    print(f"- Project line coverage: {baseline_total:.2%} -> {final_total:.2%}")
