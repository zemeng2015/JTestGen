import unittest
import sys
from pathlib import Path

from javatestgen.runner import MavenRunner


class RunnerTests(unittest.TestCase):
    def test_non_ascii_and_invalid_log_bytes_do_not_abort_command(self) -> None:
        runner = MavenRunner(Path("."))
        result = runner._run([
            sys.executable, "-c",
            "import sys; sys.stdout.buffer.write('验证 §'.encode('utf-8') + b'\\xff'); sys.stdout.flush(); sys.stderr.buffer.write(b' failure detail'); sys.exit(7)",
        ])
        self.assertEqual(result.returncode, 7)
        self.assertFalse(result.ok)
        self.assertIn("验证 §", result.output)
        self.assertIn("\ufffd", result.output)
        self.assertIn("failure detail", result.output)

    def test_verify_and_test_command_include_extra_args(self) -> None:
        runner = MavenRunner(Path("."), maven_command="mvn", verify_args=("-DskipITs",))

        self.assertTrue(runner.verify_command().endswith("mvn -q -DskipITs verify"))
        self.assertTrue(
            runner.test_generated_class_command("ExampleGeneratedTest").endswith(
                "mvn -q -DskipITs -Dtest=ExampleGeneratedTest test"
            )
        )


if __name__ == "__main__":
    unittest.main()
