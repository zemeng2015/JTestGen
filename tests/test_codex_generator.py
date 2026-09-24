import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from javatestgen.codex_generator import CodexCliGenerator
from javatestgen.generator import GenerationError, GenerationRequest


class CodexCliGeneratorTests(unittest.TestCase):
    def test_generates_from_stdin_in_temporary_directory_and_cleans_output(self):
        with tempfile.TemporaryDirectory() as project_dir:
            project = Path(project_dir)
            (project / "AGENTS.md").write_text("Must not be read", encoding="utf-8")
            observed = {}

            def run(command, **kwargs):
                observed.update(command=command, **kwargs)
                output = Path(command[command.index("--output-last-message") + 1])
                self.assertEqual(output.parent, Path(kwargs["cwd"]))
                self.assertNotEqual(output.parent, project)
                self.assertFalse((output.parent / "AGENTS.md").exists())
                output.write_text("  class UnicodeTest { /* 测试 */ }\n", encoding="utf-8")
                observed["output"] = output
                return subprocess.CompletedProcess(command, 0)

            with patch("javatestgen.codex_generator.subprocess.run", side_effect=run):
                result = CodexCliGenerator(project).generate(
                    GenerationRequest("Use JUnit", "class Subject {} ; $(echo secret)")
                )

        self.assertEqual(result, "class UnicodeTest { /* 测试 */ }")
        command = observed["command"]
        self.assertEqual(command[:4], ["codex", "exec", "--sandbox", "read-only"])
        self.assertEqual(command[-1], "-")
        self.assertNotIn("--model", command)
        self.assertIn("--ignore-user-config", command)
        self.assertIn("--ephemeral", command)
        self.assertIn("features.shell_tool=false", command)
        self.assertIn("features.unified_exec=false", command)
        self.assertIn("features.apps=false", command)
        self.assertIn("features.multi_agent=false", command)
        self.assertIn('web_search="disabled"', command)
        self.assertIn("Use JUnit", observed["input"])
        self.assertIn("$(echo secret)", observed["input"])
        self.assertNotIn("$(echo secret)", " ".join(command))
        self.assertIn("Do not use any tools", observed["input"])
        self.assertFalse(observed["shell"])
        self.assertEqual(observed["timeout"], 180)
        self.assertFalse(observed["output"].parent.exists())

    def test_explicit_executable_model_and_timeout(self):
        def run(command, **kwargs):
            self.assertEqual(command[0], "/tools/codex")
            self.assertEqual(command[command.index("--model") + 1], "selected-model")
            self.assertEqual(kwargs["timeout"], 25)
            Path(command[command.index("--output-last-message") + 1]).write_text("class T {}")
            return subprocess.CompletedProcess(command, 0)

        with patch("javatestgen.codex_generator.subprocess.run", side_effect=run):
            CodexCliGenerator(Path("."), "selected-model", "/tools/codex", 25).generate(
                GenerationRequest("", "")
            )

    def test_nonzero_exit_does_not_expose_stderr_or_return_partial_response(self):
        output_paths = []

        def run(command, **kwargs):
            output = Path(command[command.index("--output-last-message") + 1])
            output_paths.append(output)
            output.write_text("partial response")
            return subprocess.CompletedProcess(command, 1, stderr="secret-token")

        with patch("javatestgen.codex_generator.subprocess.run", side_effect=run):
            with self.assertRaises(GenerationError) as caught:
                CodexCliGenerator(Path(".")).generate(GenerationRequest("", ""))
        self.assertNotIn("secret-token", str(caught.exception))
        self.assertIn("exit 1", str(caught.exception))
        self.assertFalse(output_paths[0].parent.exists())

    def test_missing_and_empty_response_fail_without_stdout_fallback(self):
        for content in (None, " \n"):
            with self.subTest(content=content):
                def run(command, **kwargs):
                    if content is not None:
                        Path(command[command.index("--output-last-message") + 1]).write_text(content)
                    return subprocess.CompletedProcess(command, 0, stdout="session logs")

                with patch("javatestgen.codex_generator.subprocess.run", side_effect=run):
                    with self.assertRaises(GenerationError):
                        CodexCliGenerator(Path(".")).generate(GenerationRequest("", ""))

    def test_timeout_and_missing_executable_are_sanitized(self):
        errors = (
            subprocess.TimeoutExpired(["codex", "private-prompt"], 180, stderr="secret"),
            FileNotFoundError("private executable path"),
        )
        for error in errors:
            with self.subTest(error=type(error).__name__):
                with patch("javatestgen.codex_generator.subprocess.run", side_effect=error):
                    with self.assertRaises(GenerationError) as caught:
                        CodexCliGenerator(Path(".")).generate(GenerationRequest("", ""))
                self.assertNotIn("private", str(caught.exception))
                self.assertNotIn("secret", str(caught.exception))
                self.assertTrue(caught.exception.__suppress_context__)

    def test_rejects_nonpositive_timeout(self):
        for timeout in (0, -1):
            with self.assertRaises(ValueError):
                CodexCliGenerator(Path("."), timeout_seconds=timeout)
