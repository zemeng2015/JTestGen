from __future__ import annotations

import re
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from .config import RunConfig
from .context import build_prompt_context
from .coverage import ClassCoverage, parse_class_coverages, parse_jacoco_xml
from .generator import GenerationError, OpenAICompatibleGenerator
from .java_source import JavaClass, discover_java_classes, find_java_class, find_java_class_by_name
from .prompting import GENERATION_PROMPT_VERSION, REPAIR_PROMPT_VERSION, build_initial_request, build_repair_request
from .reporting import RunArtifacts
from .path_safety import require_project_path
from .runner import MavenRunner
from .targeting import build_target_candidates, pick_target_candidate, rank_target_candidates


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
        self.artifacts = RunArtifacts(config.project, enabled=config.save_artifacts)
        self.artifacts.report.prompt_versions = {
            "generation": GENERATION_PROMPT_VERSION,
            "repair": REPAIR_PROMPT_VERSION,
        }
        self.artifacts.flush()

    def run(self) -> int:
        started = time.monotonic()
        self.artifacts.update(
            verify_command=self.runner.verify_command(),
        )
        if self.config.max_targets < 1:
            raise ValueError("--max-targets must be at least 1")
        _validate_project(self.config.project)
        classes = discover_java_classes(self.config.main_source_root, self.config.class_glob)
        if not classes:
            print(f"No Java classes found under {self.config.main_source_root}")
            self._finish(status="no_java_classes", started=started)
            return 1

        print("Running baseline coverage: mvn -q verify")
        if self.config.strict_verification:
            clear_coverage_evidence(self.config.project)
        baseline_result = self.runner.verify()
        self.artifacts.write_text("maven.baseline.log", baseline_result.output)
        if not baseline_result.ok:
            print("Baseline mvn verify failed. Fix the target project before generating new tests.")
            print(baseline_result.output[-4000:])
            self.artifacts.update(status="baseline_failed")
            self.artifacts.add_error("Baseline mvn verify failed.")
            self._finish(status="baseline_failed", started=started)
            return 1

        self.artifacts.update(baseline_verified=True)
        baseline_summary = parse_jacoco_xml(self.config.jacoco_xml)
        baseline_coverages = parse_class_coverages(self.config.jacoco_xml)
        selected_targets = self._select_target_classes(classes, baseline_coverages)
        if not selected_targets:
            print(f"No coverable class found in {self.config.jacoco_xml}")
            self._finish(status="no_coverable_class", started=started)
            return 1

        first_class, first_coverage = selected_targets[0]
        self.artifacts.update(
            target_class=", ".join(java_class.qualified_name for java_class, _ in selected_targets),
            baseline_project_line_coverage=baseline_summary.line_ratio,
            baseline_class_line_coverage=first_coverage.line_ratio,
        )

        generated_paths: list[Path] = []
        processed: list[tuple[JavaClass, ClassCoverage]] = []
        for index, (java_class, class_coverage) in enumerate(selected_targets, start=1):
            print(
                f"Selected target {index}/{len(selected_targets)}: "
                f"{java_class.qualified_name} with {class_coverage.line_ratio:.2%} line coverage "
                f"({class_coverage.line_covered} covered, {class_coverage.line_missed} missed)"
            )
            test_path = self._process_class(java_class, class_coverage, artifact_prefix=_artifact_prefix(index))
            if test_path is None:
                self._finish(status=self.artifacts.report.status, started=started)
                return 1
            generated_paths.append(test_path)
            processed.append((java_class, class_coverage))

        print("Running final coverage: mvn -q verify")
        if self.config.strict_verification:
            clear_coverage_evidence(self.config.project)
            clear_test_evidence(self.config.project)
        final_result = self.runner.verify()
        self.artifacts.write_text("maven.final.log", final_result.output)
        if not final_result.ok:
            print("Final mvn verify failed after generation.")
            print(final_result.output[-4000:])
            self.artifacts.update(status="final_verify_failed")
            self.artifacts.add_error("Final mvn verify failed after generation.")
            self._finish(status="final_verify_failed", started=started)
            return 1

        if self.config.strict_verification:
            count = executed_tests(self.config.project)
            if count <= 0 or any(executed_tests(self.config.project, path.stem) <= 0 for path in generated_paths):
                self.artifacts.add_error("Final verification has no fresh passing executed Surefire tests.")
                self._finish(status="final_evidence_missing", started=started)
                return 1
            self.artifacts.update(final_tests_executed=count)
        self.artifacts.update(final_verified=True)
        final_summary = parse_jacoco_xml(self.config.jacoco_xml)
        final_coverages = parse_class_coverages(self.config.jacoco_xml)
        first_final_coverage = self._find_class_coverage(first_class, final_coverages)
        for java_class, class_coverage in processed:
            final_class_coverage = self._find_class_coverage(java_class, final_coverages)
            print_generation_report(
                java_class=java_class,
                before=class_coverage,
                after=final_class_coverage,
                baseline_total=baseline_summary.line_ratio,
                final_total=final_summary.line_ratio,
            )
        self.artifacts.update(
            status="success",
            final_project_line_coverage=final_summary.line_ratio,
            final_class_line_coverage=first_final_coverage.line_ratio,
            project_line_coverage_delta=final_summary.line_ratio - baseline_summary.line_ratio,
            class_line_coverage_delta=first_final_coverage.line_ratio - first_coverage.line_ratio,
        )

        if final_summary.line_ratio < self.config.target_coverage:
            print(
                f"Coverage below target: {final_summary.line_ratio:.2%} < "
                f"{self.config.target_coverage:.2%}"
            )
            self.artifacts.update(status="coverage_below_target")
            self._finish(status="coverage_below_target", started=started)
            return 1
        if self.config.patch_output and not self.config.dry_run:
            self._write_patch(generated_paths)
        self._finish(status="success", started=started)
        return 0

    def _finish(self, status: str, started: float) -> None:
        self.artifacts.update(
            status=status,
            duration_seconds=round(time.monotonic() - started, 3),
        )

    def _select_target_classes(
        self,
        classes: list[JavaClass],
        coverages: list[ClassCoverage],
    ) -> list[tuple[JavaClass, ClassCoverage]]:
        if self.config.target_class:
            java_class = find_java_class_by_name(classes, self.config.target_class)
            if java_class is None:
                raise ValueError(f"--target-class was not found under {self.config.main_source_root}: {self.config.target_class}")
            return [(java_class, self._find_class_coverage(java_class, coverages))]

        candidates = rank_target_candidates(build_target_candidates(classes, coverages), limit=self.config.max_targets)
        if not candidates:
            candidate = pick_target_candidate(build_target_candidates(classes, coverages))
            return [] if candidate is None else [(candidate.java_class, candidate.coverage)]
        return [(candidate.java_class, candidate.coverage) for candidate in candidates]

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

    def _process_class(self, java_class: JavaClass, coverage: ClassCoverage, artifact_prefix: str = "") -> Path | None:
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
        self.artifacts.update(generated_test_path=relative_test_path)
        self.artifacts.update(test_command=self.runner.test_generated_class_command(test_class_name))
        self.artifacts.write_text(f"{artifact_prefix}prompt.initial.system.txt", request.system_prompt)
        self.artifacts.write_text(f"{artifact_prefix}prompt.initial.user.txt", request.user_prompt)

        print(f"Generating {test_path.relative_to(self.config.project)} for {java_class.qualified_name}")
        if self.config.dry_run:
            print(request.user_prompt)
            return test_path

        try:
            generated = clean_java_source(self.generator.generate(request))
        except GenerationError as exc:
            print(exc)
            self.artifacts.update(status="generation_failed")
            self.artifacts.add_error(str(exc))
            return None

        write_test(test_path, generated, self.config.project)
        self.artifacts.write_text(f"{artifact_prefix}generated.initial.java", generated)

        for attempt in range(self.config.max_repairs + 1):
            if self.config.strict_verification:
                clear_test_evidence(self.config.project, test_class_name)
            result = self.runner.test_generated_class(test_class_name)
            self.artifacts.write_text(f"{artifact_prefix}maven.test.{attempt}.log", result.output)
            if result.ok:
                if self.config.strict_verification:
                    count = executed_tests(self.config.project, test_class_name)
                    if count <= 0:
                        self.artifacts.update(status="generated_evidence_missing")
                        self.artifacts.add_error("Generated test command produced no fresh passing executed Surefire tests.")
                        return None
                    self.artifacts.update(generated_tests_executed=count)
                self.artifacts.update(generated_verified=True)
                print(f"Generated test passed: mvn -q -Dtest={test_class_name} test")
                self.artifacts.write_text(f"{artifact_prefix}generated.final.java", test_path.read_text(encoding="utf-8"))
                return test_path

            if attempt >= self.config.max_repairs:
                print(f"Repair limit reached for {test_class_name}")
                print(result.output[-4000:])
                self.artifacts.update(status="repair_limit_reached", repair_attempts=attempt)
                self.artifacts.add_error(f"Repair limit reached for {test_class_name}.")
                return None

            print(f"Repairing {test_class_name}, attempt {attempt + 1}/{self.config.max_repairs}")
            self.artifacts.update(repair_attempts=attempt + 1)
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
            self.artifacts.write_text(f"{artifact_prefix}prompt.repair.{attempt + 1}.system.txt", repair_request.system_prompt)
            self.artifacts.write_text(f"{artifact_prefix}prompt.repair.{attempt + 1}.user.txt", repair_request.user_prompt)
            try:
                repaired = clean_java_source(self.generator.generate(repair_request))
            except GenerationError as exc:
                print(exc)
                self.artifacts.update(status="generation_failed")
                self.artifacts.add_error(str(exc))
                return None
            write_test(test_path, repaired, self.config.project)
            self.artifacts.write_text(f"{artifact_prefix}generated.repair.{attempt + 1}.java", repaired)
        return None

    def _write_patch(self, paths: list[Path]) -> None:
        if not paths:
            return
        relative_paths = [str(path.relative_to(self.config.project)) for path in paths]
        patch_parts: list[str] = []
        errors: list[str] = []
        for relative_path, path in zip(relative_paths, paths, strict=True):
            if _is_git_tracked(self.config.project, relative_path):
                completed = subprocess.run(
                    ["git", "diff", "--", relative_path],
                    cwd=self.config.project,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    check=False,
                )
                if completed.returncode == 0:
                    patch_parts.append(completed.stdout)
                else:
                    errors.append(f"Patch generation failed for {relative_path} with exit code {completed.returncode}.")
            else:
                patch_parts.append(format_new_file_patch(relative_path, path.read_text(encoding="utf-8")))
        output_path = self.config.patch_output
        if output_path is None:
            return
        output_path.parent.mkdir(parents=True, exist_ok=True)
        patch = "\n".join(part.rstrip() for part in patch_parts if part).rstrip() + "\n"
        output_path.write_text(patch, encoding="utf-8")
        self.artifacts.write_text("generated.patch", patch)
        for error in errors:
            self.artifacts.add_error(error)
        print(f"Patch written to: {output_path}")


def write_test(path: Path, source: str, project: Path | None = None) -> None:
    if project is not None:
        require_project_path(project, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.rstrip() + "\n", encoding="utf-8", newline="\n")


def clear_coverage_evidence(project: Path) -> None:
    for relative in ("target/site/jacoco/jacoco.xml", "target/jacoco.exec"):
        path = project / relative
        require_project_path(project, path)
        path.unlink(missing_ok=True)


def test_report_paths(project: Path, class_name: str | None = None) -> list[Path]:
    directory = project / "target/surefire-reports"
    require_project_path(project, directory)
    paths = list(directory.glob("TEST-*.xml"))
    if class_name:
        paths = [p for p in paths if p.stem.removeprefix("TEST-").split(".")[-1] == class_name]
    return paths


def clear_test_evidence(project: Path, class_name: str | None = None) -> None:
    for path in test_report_paths(project, class_name):
        require_project_path(project, path)
        path.unlink()


def executed_tests(project: Path, class_name: str | None = None) -> int:
    count = 0
    for path in test_report_paths(project, class_name):
        if path.is_symlink():
            return 0
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            return 0
        if any(int(suite.get("failures", "0")) or int(suite.get("errors", "0")) for suite in root.iter("testsuite")):
            return 0
        cases = list(root.iter("testcase"))
        if any(case.find("failure") is not None or case.find("error") is not None for case in cases):
            return 0
        count += sum(case.find("skipped") is None for case in cases)
    return count


def clean_java_source(source: str) -> str:
    cleaned = source.strip()
    fence = re.fullmatch(r"```(?:java)?\s*(.*?)```", cleaned, flags=re.DOTALL)
    return fence.group(1).strip() if fence else cleaned


def _artifact_prefix(index: int) -> str:
    return "" if index == 1 else f"target-{index}."


def _is_git_tracked(project: Path, relative_path: str) -> bool:
    completed = subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative_path],
        cwd=project,
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return completed.returncode == 0


def format_new_file_patch(relative_path: str, content: str) -> str:
    normalized = relative_path.replace("\\", "/")
    lines = content.rstrip("\n").splitlines()
    body = "\n".join(f"+{line}" for line in lines)
    return (
        f"diff --git a/{normalized} b/{normalized}\n"
        "new file mode 100644\n"
        "index 0000000..0000000\n"
        "--- /dev/null\n"
        f"+++ b/{normalized}\n"
        f"@@ -0,0 +1,{len(lines)} @@\n"
        f"{body}\n"
    )


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
