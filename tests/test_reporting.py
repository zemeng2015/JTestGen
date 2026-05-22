import json
import tempfile
import unittest
from pathlib import Path

from javatestgen.reporting import RunArtifacts


class ReportingTests(unittest.TestCase):
    def test_report_json_contains_self_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifacts = RunArtifacts(Path(temp_dir))
            artifacts.update(status="success")
            report_path = artifacts.root / "report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(report["artifacts"]["report.json"], str(report_path))

    def test_run_ids_are_unique_for_fast_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            first = RunArtifacts(Path(temp_dir))
            second = RunArtifacts(Path(temp_dir))

        self.assertNotEqual(first.run_id, second.run_id)


if __name__ == "__main__":
    unittest.main()
