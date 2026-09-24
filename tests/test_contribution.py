import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from javatestgen.cli import build_parser
from javatestgen.config import RunConfig
from javatestgen.contribution import (ContributionError, command, digest, prepare,
                                      publish, repository_name, save, summary, validate, validate_commit)
from javatestgen.runner import MavenRunner
from javatestgen.workflow import clear_coverage_evidence, clear_test_evidence, executed_tests, write_test
from javatestgen.reporting import RunArtifacts


class ContributionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name)
        self.repo = self.workspace / "repo"
        self.repo.mkdir()
        command(["git", "init"], self.repo)
        command(["git", "config", "user.email", "test@example.invalid"], self.repo)
        command(["git", "config", "user.name", "Test"], self.repo)
        command(["git", "config", "commit.gpgsign", "false"], self.repo)
        command(["git", "remote", "add", "origin", "https://github.com/example/project.git"], self.repo)
        (self.repo / "pom.xml").write_text("<project/>")
        command(["git", "add", "pom.xml"], self.repo)
        command(["git", "commit", "-m", "baseline"], self.repo)
        self.relative = "src/test/java/example/ExampleJTestGenTest.java"
        self.test = self.repo / self.relative
        self.test.parent.mkdir(parents=True)
        self.test.write_text("class ExampleJTestGenTest {}\n", newline="\n")
        self.report_path = self.repo / ".jtestgen/runs/test/report.json"
        self.report_path.parent.mkdir(parents=True)
        self.report = dict(status="success", target_class="example.Example", generated_test_path=self.relative,
                           baseline_verified=True, generated_verified=True, final_verified=True,
                           baseline_class_line_coverage=0.5, final_class_line_coverage=0.75,
                           baseline_project_line_coverage=0.5, final_project_line_coverage=0.55,
                           generated_tests_executed=3, final_tests_executed=20, repair_attempts=1, verify_command="C:/private/mvn -Dtoken=secret verify",
                           test_command="C:/private/mvn -Dpassword=secret -Dtest=ExampleJTestGenTest test")
        save(self.report_path, self.report)
        self.manifest_path = self.workspace / "contribution.json"
        self.manifest = dict(version=1, repository="example/project", status="prepared", module=".",
                             base_sha=command(["git", "rev-parse", "HEAD"], self.repo), base_branch="main",
                             branch="jtestgen/1234567890-12345678", files={self.relative: digest(self.test)},
                             report_path=self.report_path.relative_to(self.repo).as_posix(),
                             report_sha256=digest(self.report_path))
        save(self.manifest_path, self.manifest)

    def test_names_reject_credentials_options_and_other_hosts(self):
        self.assertEqual(repository_name("https://github.com/a/b.git"), "a/b")
        for value in ("--help", "https://token@github.com/a/b", "https://other/a/b", "a/b/../../c", "a/b?token=x"):
            with self.subTest(value=value), self.assertRaises(ContributionError):
                repository_name(value)

    def test_real_git_manifest_and_summary(self):
        validate(self.manifest_path)
        body = summary(self.manifest, self.report)
        self.assertIn("50.00% | 75.00%", body)
        self.assertNotIn("secret", body)
        self.assertNotIn("private", body)
        self.assertIn("human", body)

    def test_changed_generated_file_blocks_publish(self):
        self.test.write_text("changed")
        with self.assertRaisesRegex(ContributionError, "changed since"):
            validate(self.manifest_path)

    def test_production_change_blocks_publish(self):
        (self.repo / "pom.xml").write_text("changed")
        with self.assertRaisesRegex(ContributionError, "Diff must"):
            validate(self.manifest_path)

    def test_report_tampering_blocks_publish(self):
        self.report_path.write_text("{}")
        with self.assertRaisesRegex(ContributionError, "Run report changed"):
            validate(self.manifest_path)

    def test_failed_or_non_improving_run_blocks_publish(self):
        for field, value in (("final_verified", False), ("final_class_line_coverage", 0.5),
                             ("final_project_line_coverage", 0.4)):
            with self.subTest(field=field):
                report = {**self.report, field: value}
                save(self.report_path, report)
                save(self.manifest_path, {**self.manifest, "report_sha256": digest(self.report_path)})
                with self.assertRaises(ContributionError):
                    validate(self.manifest_path)

    def test_existing_directory_never_overwritten(self):
        with self.assertRaises(FileExistsError):
            prepare("a/b", self.workspace, RunConfig(project=self.repo))
        self.assertTrue((self.repo / "pom.xml").exists())

    def test_module_and_jacoco_cli(self):
        args = build_parser().parse_args(["contribute", "a/b", "--workspace", "new", "--module", "core", "--jacoco"])
        self.assertEqual(args.test_suffix, "JTestGenTest")
        self.assertTrue(args.jacoco)
        runner = MavenRunner(self.repo, jacoco=True)
        goals = runner._verify_argv()
        self.assertLess(goals.index("verify"), goals.index("org.jacoco:jacoco-maven-plugin:0.8.14:report"))

    def test_draft_publish_and_uncertain_creation_retry_without_duplicates(self):
        calls = []
        created = False

        def fake(argv, cwd):
            nonlocal created
            calls.append(argv)
            if argv[:3] == ["gh", "api", "user"]:
                return "contributor"
            if argv[:3] == ["gh", "pr", "list"]:
                self.assertEqual(argv[argv.index("--head") + 1], self.manifest["branch"])
                self.assertIn("headRepositoryOwner", argv[argv.index("--json") + 1])
                unrelated = dict(url="https://github.com/example/project/pull/999", state="OPEN",
                                 headRefOid="unrelated", headRepositoryOwner=dict(login="another-fork-owner"))
                if created:
                    sha = command(["git", "rev-parse", "HEAD"], self.repo)
                    return json.dumps([unrelated, dict(url="https://github.com/example/project/pull/1", state="OPEN", headRefOid=sha,
                                                       headRepositoryOwner=dict(login="CONTRIBUTOR"))])
                return json.dumps([unrelated])
            if argv[:3] == ["gh", "repo", "fork"]:
                self.assertEqual(argv, ["gh", "repo", "fork", "example/project", "--clone=false"])
                return ""
            if argv[:2] == ["gh", "api"]:
                return json.dumps(dict(fork=True, parent=dict(full_name="example/project")))
            if argv[:2] == ["git", "push"]:
                self.assertNotIn("--force", argv)
                return ""
            if argv[:3] == ["gh", "pr", "create"]:
                self.assertIn("--draft", argv)
                created = True
                raise ContributionError("Connection lost after server created PR")
            return command(argv, cwd)

        with patch("javatestgen.contribution.command", side_effect=fake):
            with self.assertRaises(ContributionError):
                publish(self.manifest_path)
            self.assertEqual(publish(self.manifest_path), 0)
        self.assertEqual(sum(c[:3] == ["gh", "pr", "create"] for c in calls), 1)
        tracked = command(["git", "show", "--pretty=", "--name-only", "HEAD"], self.repo)
        self.assertEqual(tracked, self.relative)
        receipt = json.loads(self.manifest_path.read_text())
        self.assertEqual(receipt["status"], "published")
        self.assertNotIn("publish_error", receipt)

    def test_unsafe_module_rejected_before_clone(self):
        with self.assertRaises(ContributionError):
            prepare("a/b", self.workspace / "new", RunConfig(project=self.repo), module="../outside")

    def test_matching_fork_with_wrong_head_refuses_duplicate_creation(self):
        calls = []

        def fake(argv, cwd):
            calls.append(argv)
            if argv[:3] == ["gh", "api", "user"]:
                return "contributor"
            if argv[:3] == ["gh", "pr", "list"]:
                return json.dumps([dict(url="https://github.com/example/project/pull/1", state="OPEN",
                                        headRefOid="changed-head", headRepositoryOwner=dict(login="contributor"))])
            return command(argv, cwd)

        with patch("javatestgen.contribution.command", side_effect=fake):
            with self.assertRaisesRegex(ContributionError, "different commit"):
                publish(self.manifest_path)
        self.assertFalse(any(c[:3] == ["gh", "pr", "create"] or c[:2] == ["git", "push"] for c in calls))

    def test_module_manifest_accepts_only_tests_under_selected_module(self):
        module = self.repo / "core"
        module.mkdir()
        self.test.rename(module / "Test.java")
        destination = module / self.relative
        destination.parent.mkdir(parents=True)
        (module / "Test.java").rename(destination)
        report_path = module / ".jtestgen/runs/test/report.json"
        report_path.parent.mkdir(parents=True)
        self.report_path.rename(report_path)
        manifest = {**self.manifest, "module": "core", "files": {"core/" + self.relative: digest(destination)},
                    "report_path": report_path.relative_to(self.repo).as_posix()}
        save(self.manifest_path, manifest)
        validate(self.manifest_path)
        (self.repo / "unrelated.java").write_text("unexpected")
        with self.assertRaisesRegex(ContributionError, "Diff must"):
            validate(self.manifest_path)

    def test_skip_tests_and_multiple_targets_rejected_before_clone(self):
        for config in (RunConfig(self.repo, verify_args=("-DskipTests",)), RunConfig(self.repo, max_targets=2)):
            with self.assertRaises(ContributionError):
                prepare("a/b", self.workspace / "new", config)

    def test_clone_failure_leaves_durable_failure_manifest(self):
        workspace = self.workspace / "failed"
        with patch("javatestgen.contribution.command", side_effect=ContributionError("clone failed")):
            with self.assertRaises(ContributionError):
                prepare("a/b", workspace, RunConfig(self.repo))
        self.assertEqual(json.loads((workspace / "contribution.json").read_text())["status"], "failed")

    def test_clone_sets_input_autocrlf_before_initial_checkout(self):
        workspace = self.workspace / "clone-check"
        with patch("javatestgen.contribution.command", side_effect=ContributionError("stop after clone args")) as mocked:
            with self.assertRaises(ContributionError):
                prepare("a/b", workspace, RunConfig(self.repo))
        self.assertEqual(mocked.call_args.args[0], [
            "git", "-c", "core.autocrlf=input", "clone", "--",
            "https://github.com/a/b.git", str(workspace / "repo"),
        ])

    def test_stale_coverage_and_surefire_are_cleared_and_skips_do_not_count(self):
        xml = self.repo / "target/site/jacoco/jacoco.xml"
        xml.parent.mkdir(parents=True)
        xml.write_text("stale")
        execution = self.repo / "target/jacoco.exec"
        execution.write_bytes(b"stale")
        surefire = self.repo / "target/surefire-reports/TEST-example.ExampleJTestGenTest.xml"
        surefire.parent.mkdir(parents=True)
        surefire.write_text('<testsuite tests="1"><testcase><skipped/></testcase></testsuite>')
        self.assertEqual(executed_tests(self.repo, "ExampleJTestGenTest"), 0)
        surefire.write_text('<testsuite tests="1"><testcase/></testsuite>')
        self.assertEqual(executed_tests(self.repo, "ExampleJTestGenTest"), 1)
        clear_test_evidence(self.repo, "ExampleJTestGenTest")
        clear_coverage_evidence(self.repo)
        self.assertFalse(xml.exists())
        self.assertFalse(execution.exists())
        self.assertEqual(executed_tests(self.repo), 0)

    def test_actual_commit_cannot_hide_production_change_by_restoring_worktree(self):
        (self.repo / "pom.xml").write_text("hook change")
        command(["git", "add", "pom.xml", self.relative], self.repo)
        command(["git", "commit", "-m", "bad hook"], self.repo)
        self.manifest["commit_sha"] = command(["git", "rev-parse", "HEAD"], self.repo)
        (self.repo / "pom.xml").write_text("<project/>")
        with self.assertRaisesRegex(ContributionError, "Actual commit"):
            validate_commit(self.manifest, self.repo)

    def test_actual_committed_test_bytes_must_match_verified_worktree(self):
        original = self.test.read_bytes()
        self.test.write_bytes(b"class Changed {}\n")
        command(["git", "add", self.relative], self.repo)
        command(["git", "commit", "-m", "filter changed"], self.repo)
        self.manifest["commit_sha"] = command(["git", "rev-parse", "HEAD"], self.repo)
        self.test.write_bytes(original)
        with self.assertRaisesRegex(ContributionError, "Committed test bytes"):
            validate_commit(self.manifest, self.repo)

    def test_formatter_crlf_normalizes_without_accepting_changed_content(self):
        command(["git", "config", "core.autocrlf", "input"], self.repo)
        # Simulate a native-line-ending formatter rewriting tracked production
        # files and the generated test, without any semantic content change.
        baseline = self.repo / "baseline.java"
        baseline.write_bytes(b"class Baseline {\n}\n")
        command(["git", "add", "baseline.java"], self.repo)
        command(["git", "commit", "-m", "LF baseline"], self.repo)
        self.manifest["base_sha"] = command(["git", "rev-parse", "HEAD"], self.repo)
        baseline.write_bytes(b"class Baseline {\r\n}\r\n")
        self.test.write_bytes(b"class ExampleJTestGenTest {}\r\n")
        self.manifest["files"][self.relative] = digest(self.test)
        save(self.manifest_path, self.manifest)
        validate(self.manifest_path)
        command(["git", "add", self.relative], self.repo)
        command(["git", "commit", "-m", "normalized generated test"], self.repo)
        self.manifest["commit_sha"] = command(["git", "rev-parse", "HEAD"], self.repo)
        validate_commit(self.manifest, self.repo)
        self.test.write_bytes(b"class MaliciousChange {}\r\n")
        with self.assertRaisesRegex(ContributionError, "Committed test bytes"):
            validate_commit(self.manifest, self.repo)

    def test_upstream_no_text_attribute_preserves_verified_crlf_bytes(self):
        command(["git", "config", "core.autocrlf", "input"], self.repo)
        (self.repo / ".gitattributes").write_bytes(b"*.java -text\n")
        command(["git", "add", ".gitattributes"], self.repo)
        command(["git", "commit", "-m", "upstream attributes"], self.repo)
        self.manifest["base_sha"] = command(["git", "rev-parse", "HEAD"], self.repo)
        self.test.write_bytes(b"class ExampleJTestGenTest {}\r\n")
        command(["git", "add", self.relative], self.repo)
        command(["git", "commit", "-m", "raw CRLF generated test"], self.repo)
        self.manifest["commit_sha"] = command(["git", "rev-parse", "HEAD"], self.repo)
        validate_commit(self.manifest, self.repo)

    def test_receipt_lost_after_commit_is_recovered_only_on_bound_branch(self):
        command(["git", "switch", "-c", self.manifest["branch"]], self.repo)
        command(["git", "add", self.relative], self.repo)
        command(["git", "commit", "-m", "verified tests"], self.repo)
        self.manifest["status"] = "publishing"
        save(self.manifest_path, self.manifest)
        recovered, _, _ = validate(self.manifest_path)
        self.assertEqual(recovered["commit_sha"], command(["git", "rev-parse", "HEAD"], self.repo))

    def test_generated_write_rejects_escape_before_creating_file(self):
        outside = self.workspace / "outside.java"
        with self.assertRaisesRegex(ValueError, "escapes"):
            write_test(outside, "class Escape {}", self.repo)
        self.assertFalse(outside.exists())

    def test_generated_write_rejects_symlink_parent_before_writing(self):
        outside = self.workspace / "outside"
        outside.mkdir()
        link = self.repo / "linked"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("Host does not grant symlink creation")
        with self.assertRaises(ValueError):
            write_test(link / "Escape.java", "class Escape {}", self.repo)
        self.assertFalse((outside / "Escape.java").exists())

    def test_artifact_and_cleanup_parent_links_rejected_before_mutation(self):
        original = Path.is_symlink
        with patch.object(Path, "is_symlink", lambda path: path.name == ".jtestgen" or original(path)):
            with self.assertRaisesRegex(ValueError, "symlinks"):
                RunArtifacts(self.repo)
        execution = self.repo / "target/jacoco.exec"
        execution.parent.mkdir()
        execution.write_bytes(b"must survive")
        with patch.object(Path, "is_symlink", lambda path: path.name == "target" or original(path)):
            with self.assertRaisesRegex(ValueError, "symlinks"):
                clear_coverage_evidence(self.repo)
        self.assertEqual(execution.read_bytes(), b"must survive")


if __name__ == "__main__":
    unittest.main()
