import json
import tempfile
import unittest
from pathlib import Path

from javatestgen.reporting import RunArtifacts, RunReport, format_summary_markdown


class ReportingTests(unittest.TestCase):
    def test_report_json_contains_self_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifacts = RunArtifacts(Path(temp_dir))
            artifacts.update(status="success")
            report_path = artifacts.root / "report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(report["artifacts"]["report.json"], str(report_path))

    def test_summary_markdown_contains_human_readable_coverage(self) -> None:
        report = RunReport(
            run_id="run-1",
            project="demo",
            status="success",
            target_class="com.example.OrderService",
            generated_test_path="src/test/java/com/example/OrderServiceGeneratedTest.java",
            baseline_class_line_coverage=0.5,
            final_class_line_coverage=0.75,
            baseline_project_line_coverage=0.6,
            final_project_line_coverage=0.7,
            class_line_coverage_delta=0.25,
            project_line_coverage_delta=0.1,
            repair_attempts=1,
            verify_command="mvn -q verify",
            test_command="mvn -q -Dtest=OrderServiceGeneratedTest test",
            prompt_versions={"generation": "generation-v7", "repair": "repair-v7"},
        )

        summary = format_summary_markdown(report)

        self.assertIn("# JTestGen Run Summary", summary)
        self.assertIn("com.example.OrderService", summary)
        self.assertIn("50.00%", summary)
        self.assertIn("75.00%", summary)
        self.assertIn("+25.00%", summary)
        self.assertIn("reviewable candidates", summary)

    def test_flush_writes_summary_markdown_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifacts = RunArtifacts(Path(temp_dir))
            artifacts.update(
                status="success",
                target_class="com.example.OrderService",
                baseline_class_line_coverage=0.5,
                final_class_line_coverage=1.0,
                class_line_coverage_delta=0.5,
            )
            summary_path = artifacts.root / "summary.md"
            report = json.loads((artifacts.root / "report.json").read_text(encoding="utf-8"))
            summary = summary_path.read_text(encoding="utf-8")

        self.assertEqual(report["artifacts"]["summary.md"], str(summary_path))
        self.assertIn("JTestGen Run Summary", summary)

    def test_run_ids_are_unique_for_fast_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            first = RunArtifacts(Path(temp_dir))
            second = RunArtifacts(Path(temp_dir))

        self.assertNotEqual(first.run_id, second.run_id)


if __name__ == "__main__":
    unittest.main()
