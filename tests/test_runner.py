import unittest
from pathlib import Path

from javatestgen.runner import MavenRunner


class RunnerTests(unittest.TestCase):
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
