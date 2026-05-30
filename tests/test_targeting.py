import unittest
from pathlib import Path

from javatestgen.coverage import ClassCoverage
from javatestgen.java_source import JavaClass
from javatestgen.targeting import build_target_candidates, pick_target_candidate, rank_target_candidates, skip_reason


class TargetingTests(unittest.TestCase):
    def test_skips_abstract_interface_and_inner_classes(self) -> None:
        abstract_class = self._java_class("AbstractThing", "package com.example; public abstract class AbstractThing {}")
        interface = self._java_class("ThingApi", "package com.example; public interface ThingApi {}")
        concrete = self._java_class("ConcreteThing", "package com.example; public class ConcreteThing {}")
        coverages = [
            self._coverage("com.example.AbstractThing", "AbstractThing.java", 0, 10),
            self._coverage("com.example.ThingApi", "ThingApi.java", 0, 10),
            self._coverage("com.example.ConcreteThing.Inner", "ConcreteThing.java", 0, 10),
            self._coverage("com.example.ConcreteThing", "ConcreteThing.java", 1, 9),
        ]

        candidates = build_target_candidates([abstract_class, interface, concrete], coverages)
        picked = pick_target_candidate(candidates)

        self.assertIsNotNone(picked)
        self.assertEqual(picked.java_class.type_name, "ConcreteThing")

    def test_skip_reason_detects_generated_source(self) -> None:
        java_class = JavaClass(
            source_path=Path("GeneratedThing.java"),
            relative_path=Path("com/example/generated/GeneratedThing.java"),
            source="package com.example.generated; public class GeneratedThing {}",
            package="com.example.generated",
            type_name="GeneratedThing",
        )

        self.assertEqual(skip_reason(java_class, self._coverage("com.example.generated.GeneratedThing", "GeneratedThing.java", 0, 3)), "generated source")

    def test_rank_target_candidates_returns_requested_limit(self) -> None:
        first = self._java_class("FirstThing", "package com.example; public class FirstThing {}")
        second = self._java_class("SecondThing", "package com.example; public class SecondThing {}")
        third = self._java_class("ThirdThing", "package com.example; public class ThirdThing {}")
        coverages = [
            self._coverage("com.example.FirstThing", "FirstThing.java", 1, 9),
            self._coverage("com.example.SecondThing", "SecondThing.java", 5, 5),
            self._coverage("com.example.ThirdThing", "ThirdThing.java", 8, 2),
        ]

        ranked = rank_target_candidates(build_target_candidates([first, second, third], coverages), limit=2)

        self.assertEqual([candidate.java_class.type_name for candidate in ranked], ["FirstThing", "SecondThing"])

    def _java_class(self, type_name: str, source: str) -> JavaClass:
        return JavaClass(
            source_path=Path(f"{type_name}.java"),
            relative_path=Path("com") / "example" / f"{type_name}.java",
            source=source,
            package="com.example",
            type_name=type_name,
        )

    def _coverage(self, qualified_name: str, source_file: str, covered: int, missed: int) -> ClassCoverage:
        return ClassCoverage(
            qualified_name=qualified_name,
            package="com.example",
            source_file=source_file,
            line_covered=covered,
            line_missed=missed,
        )


if __name__ == "__main__":
    unittest.main()
