"""Isolated GitHub contribution preparation and explicit, resumable draft publishing."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import uuid
from dataclasses import replace
from pathlib import Path, PurePosixPath

from .config import RunConfig
from .generator import OpenAICompatibleGenerator
from .runner import MavenRunner
from .workflow import TestGenerationWorkflow
from .path_safety import require_project_path


class ContributionError(ValueError):
    pass


def make_generator(config: RunConfig):
    if config.generator == "codex":
        from .codex_generator import CodexCliGenerator
        return CodexCliGenerator(config.project, model_override=config.model)
    return OpenAICompatibleGenerator(model_override=config.model)


def repository_name(value: str) -> str:
    value = value.removeprefix("https://github.com/").removesuffix(".git")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9][A-Za-z0-9_.-]*", value):
        raise ContributionError("Use a GitHub owner/repo or credential-free HTTPS GitHub URL.")
    return value


def command(argv: list[str], cwd: Path) -> str:
    result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        # Raw subprocess output can contain authenticated URLs. Keep it out of receipts.
        raise ContributionError(f"{argv[0]} {argv[1]} failed (exit {result.returncode}); inspect locally and retry.")
    return result.stdout.strip()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, data: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def test_path(project: Path, relative: str, module: str = ".") -> Path:
    parts = PurePosixPath(relative).parts
    if ("\\" in relative or ".." in parts or not relative.startswith(("" if module == "." else module + "/") + "src/test/java/")
            or not relative.endswith(".java")):
        raise ContributionError("Only Java files under src/test/java may be published.")
    path = project.joinpath(*parts)
    require_project_path(project, path)
    if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(project.resolve()):
        raise ContributionError("Generated file is missing or is not a regular in-repository test file.")
    return path


def check_report(report: dict) -> None:
    if report.get("status") != "success" or not all(report.get(k) is True for k in (
            "baseline_verified", "generated_verified", "final_verified")):
        raise ContributionError("Baseline, generated tests and final verification must all pass.")
    if report.get("generated_tests_executed", 0) <= 0 or report.get("final_tests_executed", 0) <= 0:
        raise ContributionError("Fresh executed Surefire tests must be recorded for generated and final checks.")
    if not report.get("target_class") or "," in report["target_class"]:
        raise ContributionError("Contribution publishing supports exactly one target class.")
    before = report.get("baseline_class_line_coverage")
    after = report.get("final_class_line_coverage")
    if not isinstance(before, (int, float)) or not isinstance(after, (int, float)) or not 0 <= before < after <= 1:
        raise ContributionError("A measured target-class coverage improvement is required.")
    project_before = report.get("baseline_project_line_coverage")
    project_after = report.get("final_project_line_coverage")
    if not isinstance(project_before, (int, float)) or not isinstance(project_after, (int, float)) or not 0 <= project_before <= project_after <= 1:
        raise ContributionError("Project coverage must not regress.")


def public_command(value: str | None) -> str:
    """Do not publish raw Maven arguments: they may contain paths or credentials."""
    jacoco = bool(value and "org.jacoco:jacoco-maven-plugin:0.8.14:prepare-agent" in value)
    prefix = "mvn -q " + ("org.jacoco:jacoco-maven-plugin:0.8.14:prepare-agent " if jacoco else "")
    if value and "-Dtest=" in value:
        match = re.search(r"-Dtest=([A-Za-z0-9_$]+)(?:\s|$)", value)
        if match:
            return f"{prefix}-Dtest={match[1]} test (additional local arguments omitted)"
    return prefix + "verify" + (" org.jacoco:jacoco-maven-plugin:0.8.14:report" if jacoco else "") + " (additional local arguments omitted)"


def summary(manifest: dict, report: dict) -> str:
    target = report["target_class"]
    if not re.fullmatch(r"[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*", target):
        raise ContributionError("Invalid target class in report.")
    return f"""## Test coverage contribution

Adds generated tests for `{target}` in `{manifest['repository']}`.
Base commit: `{manifest['base_sha']}`.
Maven module: `{manifest.get('module', '.')}`.

| Line coverage | Before | After |
| --- | ---: | ---: |
| Target class | {report['baseline_class_line_coverage']:.2%} | {report['final_class_line_coverage']:.2%} |
| Project | {report['baseline_project_line_coverage']:.2%} | {report['final_project_line_coverage']:.2%} |

Baseline and final verification passed. Redacted command outline: `{public_command(report.get('verify_command'))}`.
Generated test check passed. Redacted command outline: `{public_command(report.get('test_command'))}`.
Fresh executed tests: generated check {report.get('generated_tests_executed', 0)}, final suite {report.get('final_tests_executed', 0)}.
Repair attempts: {int(report['repair_attempts'])}.

Generated with JTestGen using the `{manifest.get('generator', 'openai')}` provider.
These are test candidates requiring human
review of assertions and repository conventions. Passing Maven and higher coverage
do not prove business correctness. No claim of maintainer acceptance is made.
Local prompts, logs, credentials and filesystem paths are not included in this PR.
"""


def changed_paths(project: Path, base: str) -> set[str]:
    tracked = command(["git", "diff", "--name-only", "-z", base, "--"], project)
    untracked = command(["git", "ls-files", "--others", "--exclude-standard", "-z"], project)
    return {p for p in tracked.split("\0") if p} | {p for p in untracked.split("\0") if p and ".jtestgen" not in PurePosixPath(p).parts}


def validate(manifest_path: Path) -> tuple[dict, dict, Path]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    project = manifest_path.parent / "repo"
    module = manifest.get("module", ".")
    if module != "." and not re.fullmatch(r"[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*", module):
        raise ContributionError("Invalid module path in manifest.")
    if not re.fullmatch(r"[0-9a-f]{40,64}", manifest.get("base_sha", "")) or not re.fullmatch(r"jtestgen/[0-9a-f]{10}-[0-9a-f]{8}", manifest.get("branch", "")):
        raise ContributionError("Invalid Git identity in manifest.")
    if repository_name(manifest["repository"]) != manifest["repository"]:
        raise ContributionError("Invalid repository identity.")
    if manifest.get("version") != 1 or manifest.get("status") not in ("prepared", "publishing", "published"):
        raise ContributionError("Manifest is not a prepared contribution.")
    require_project_path(project, project / manifest["report_path"])
    report_path = (project / manifest["report_path"]).resolve()
    if not report_path.is_relative_to((project / manifest.get("module", ".") / ".jtestgen/runs").resolve()) or digest(report_path) != manifest["report_sha256"]:
        raise ContributionError("Run report changed or escaped the artifact directory.")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    check_report(report)
    if command(["git", "remote", "get-url", "origin"], project) != f"https://github.com/{manifest['repository']}.git":
        raise ContributionError("Clone origin does not match the prepared repository.")
    head = command(["git", "rev-parse", "HEAD"], project)
    recovered_commit = False
    if head not in (manifest["base_sha"], manifest.get("commit_sha")):
        if (manifest["status"] == "publishing" and not manifest.get("commit_sha")
                and command(["git", "branch", "--show-current"], project) == manifest["branch"]):
            manifest["commit_sha"] = head
            recovered_commit = True
        else:
            raise ContributionError("Checkout HEAD changed after validation.")
    files = manifest["files"]
    if len(files) != 1 or (("" if manifest.get("module", ".") == "." else manifest["module"] + "/") + report["generated_test_path"].replace("\\", "/")) not in files:
        raise ContributionError("Generated file does not match the run report.")
    for relative, expected in files.items():
        if digest(test_path(project, relative, manifest.get("module", "."))) != expected:
            raise ContributionError("Generated tests changed since verification. Prepare a new run.")
    if changed_paths(project, manifest["base_sha"]) != set(files):
        raise ContributionError("Diff must contain exactly the verified generated tests, and no other files.")
    staged = command(["git", "diff", "--cached", "--name-only", "-z"], project)
    if any(p and p not in files for p in staged.split("\0")):
        raise ContributionError("Index contains files outside the verified tests.")
    if recovered_commit:
        validate_commit(manifest, project)
        save(manifest_path, manifest)
    return manifest, report, project


def prepare(repository: str, workspace: Path, config: RunConfig, create_pr: bool = False, module: str = ".") -> int:
    repository = repository_name(repository)
    if module != "." and (not re.fullmatch(r"[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*", module)):
        raise ContributionError("Module must be a safe repository-relative directory.")
    if config.max_targets != 1 or config.dry_run or not config.save_artifacts:
        raise ContributionError("contribute requires one target, real verification and saved artifacts.")
    if any(re.search(r"skip|maven\.test\.failure\.ignore", arg, re.I) and not arg.endswith("=false") for arg in config.verify_args):
        raise ContributionError("Contribution verification must not skip tests or ignore failures.")
    if not re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", config.test_suffix):
        raise ContributionError("Test suffix must be a Java identifier.")
    workspace.mkdir(parents=True, exist_ok=False)
    manifest_path = workspace / "contribution.json"
    manifest = {"version": 1, "repository": repository, "status": "started", "module": module,
                "generator": config.generator, "model": config.model or "provider default"}
    save(manifest_path, manifest)
    try:
        project = workspace / "repo"
        command(["git", "clone", "--", f"https://github.com/{repository}.git", str(project)], workspace)
        command(["git", "config", "core.autocrlf", "false"], project)
        base_sha = command(["git", "rev-parse", "HEAD"], project)
        branch = command(["git", "branch", "--show-current"], project)
        if not branch:
            raise ContributionError("Clone has no default branch.")
        # Keep local evidence out of the index even if upstream does not ignore it.
        with (project / ".git/info/exclude").open("a", encoding="utf-8") as handle:
            handle.write("\n.jtestgen/\n")
        module_project = project / module
        if not module_project.resolve().is_relative_to(project.resolve()) or any(p.is_symlink() for p in [module_project, *module_project.parents] if p != project.parent):
            raise ContributionError("Module cannot resolve outside the repository or through symlinks.")
        config = replace(config, project=module_project, patch_output=None, strict_verification=True)
        if any(config.test_source_root.rglob(f"*{config.test_suffix}.java")):
            raise ContributionError("Test suffix collides with existing tests; choose a unique --test-suffix.")
        generator = make_generator(config)
        manifest["model"] = getattr(generator, "model", None) or config.model or "provider default"
        save(manifest_path, manifest)
        workflow = TestGenerationWorkflow(config, generator,
                                          MavenRunner(module_project, config.maven_command, config.verify_args, config.jacoco))
        if workflow.run() != 0:
            raise ContributionError("Generation or verification failed. Local run artifacts were retained.")
        report_path = workflow.artifacts.root / "report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        check_report(report)
        relative = (("" if module == "." else module + "/") + report["generated_test_path"].replace("\\", "/"))
        manifest.update(status="prepared", base_sha=base_sha, base_branch=branch,
                        branch=f"jtestgen/{base_sha[:10]}-{uuid.uuid4().hex[:8]}",
                        report_path=report_path.relative_to(project).as_posix(), report_sha256=digest(report_path),
                        files={relative: digest(test_path(project, relative, manifest.get("module", ".")))})
        save(manifest_path, manifest)
        validate(manifest_path)
        (workspace / "pr-summary.md").write_text(summary(manifest, report), encoding="utf-8")
    except Exception as exc:
        manifest.update(status="failed", error=str(exc))
        save(manifest_path, manifest)
        raise
    print(f"Prepared verified contribution: {manifest_path}")
    return publish(manifest_path) if create_pr else 0


def publish(manifest_path: Path) -> int:
    manifest, report, project = validate(manifest_path)
    try:
        login = command(["gh", "api", "user", "--jq", ".login"], project)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*", login):
            raise ContributionError("Could not validate GitHub account.")
        repository = manifest["repository"]
        # Persist identity before any remote mutation, so retries cannot change authors.
        if manifest.get("publisher") not in (None, login):
            raise ContributionError("GitHub account differs from the original publish attempt.")
        manifest.update(publisher=login, status="publishing")
        save(manifest_path, manifest)
        head = f"{login}:{manifest['branch']}"
        existing = json.loads(command(["gh", "pr", "list", "--repo", repository, "--head", head,
                                      "--state", "all", "--json", "url,state,headRefOid"], project))
        if existing:
            match = existing[0]
            if match["state"] != "OPEN" or match["headRefOid"] != manifest.get("commit_sha"):
                raise ContributionError("Existing PR is closed or has a different commit; refusing a duplicate.")
            manifest.update(status="published", pr_url=match["url"])
            save(manifest_path, manifest)
            print(match["url"])
            return 0
        if not manifest.get("commit_sha"):
            current_branch = command(["git", "branch", "--show-current"], project)
            if current_branch != manifest["branch"]:
                command(["git", "switch", "-c", manifest["branch"]], project)
            command(["git", "add", "--", *manifest["files"]], project)
            command(["git", "commit", "-m", f"test: improve coverage for {report['target_class']}"], project)
            manifest["commit_sha"] = command(["git", "rev-parse", "HEAD"], project)
            save(manifest_path, manifest)
        validate(manifest_path)
        validate_commit(manifest, project)
        command(["gh", "repo", "fork", repository, "--clone=false", "--remote=false"], project)
        fork = json.loads(command(["gh", "api", f"repos/{login}/{repository.split('/')[1]}"], project))
        if not fork.get("fork") or fork.get("parent", {}).get("full_name", "").lower() != repository.lower():
            raise ContributionError("Destination is not a fork of the target repository.")
        remote = f"https://github.com/{login}/{repository.split('/')[1]}.git"
        command(["git", "push", remote, f"{manifest['commit_sha']}:refs/heads/{manifest['branch']}"], project)
        body_path = manifest_path.parent / "pr-summary.md"
        body_path.write_text(summary(manifest, report), encoding="utf-8")
        url = command(["gh", "pr", "create", "--repo", repository, "--base", manifest["base_branch"],
                       "--head", head, "--draft", "--title", f"test: improve coverage for {report['target_class']}",
                       "--body-file", str(body_path)], project)
        if not re.fullmatch(r"https://github.com/[^/]+/[^/]+/pull/\d+", url):
            raise ContributionError("PR creation response was uncertain; retry publish to reconcile it.")
        manifest.update(status="published", pr_url=url)
        manifest.pop("publish_error", None)
        save(manifest_path, manifest)
        print(url)
        return 0
    except Exception as exc:
        manifest["publish_error"] = str(exc)
        save(manifest_path, manifest)
        raise


def validate_commit(manifest: dict, project: Path) -> None:
    commit = manifest["commit_sha"]
    parents = command(["git", "rev-list", "--parents", "-n", "1", commit], project).split()
    if parents != [commit, manifest["base_sha"]]:
        raise ContributionError("Publication commit must be a single direct child of the verified base.")
    paths = command(["git", "diff", "--name-only", "-z", manifest["base_sha"], commit, "--"], project)
    if {p for p in paths.split("\0") if p} != set(manifest["files"]):
        raise ContributionError("Actual commit contains files outside the verified tests.")
    for relative in manifest["files"]:
        path = test_path(project, relative, manifest.get("module", "."))
        expected_blob = command(["git", "hash-object", "--no-filters", str(path)], project)
        tree = command(["git", "ls-tree", commit, "--", relative], project).split()
        if len(tree) < 3 or tree[0] != "100644" or tree[1] != "blob" or tree[2] != expected_blob:
            raise ContributionError("Committed test bytes differ from the verified test (hook/filter may have changed them).")
