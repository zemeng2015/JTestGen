import tempfile
import unittest
from pathlib import Path

from javatestgen.coverage import parse_class_coverages, pick_lowest_coverage_class


class CoverageTests(unittest.TestCase):
    def test_picks_zero_coverage_class_first(self) -> None:
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<report name="sample">
  <package name="com/example">
    <class name="com/example/Covered" sourcefilename="Covered.java">
      <counter type="LINE" missed="1" covered="9"/>
    </class>
    <class name="com/example/Zero" sourcefilename="Zero.java">
      <counter type="LINE" missed="10" covered="0"/>
    </class>
  </package>
</report>
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "jacoco.xml"
            path.write_text(xml, encoding="utf-8")
            coverages = parse_class_coverages(path)

        picked = pick_lowest_coverage_class(coverages)

        self.assertIsNotNone(picked)
        self.assertEqual(picked.qualified_name, "com.example.Zero")
        self.assertEqual(picked.line_ratio, 0.0)

    def test_summary_uses_root_line_counter_without_double_counting(self) -> None:
        from javatestgen.coverage import parse_jacoco_xml

        xml = """<?xml version="1.0" encoding="UTF-8"?>
<report name="sample">
  <package name="com/example">
    <class name="com/example/Covered" sourcefilename="Covered.java">
      <counter type="LINE" missed="1" covered="9"/>
    </class>
    <counter type="LINE" missed="1" covered="9"/>
  </package>
  <counter type="LINE" missed="1" covered="9"/>
</report>
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "jacoco.xml"
            path.write_text(xml, encoding="utf-8")
            summary = parse_jacoco_xml(path)

        self.assertEqual(summary.line_covered, 9)
        self.assertEqual(summary.line_missed, 1)


if __name__ == "__main__":
    unittest.main()
