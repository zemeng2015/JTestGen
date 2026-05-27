# Benchmarks

Benchmark results should demonstrate:

- real Java repositories
- reproducible Maven commands
- target class before/after coverage
- Maven pass/fail result
- repair attempts
- generated artifact path

Completed benchmark rows require both:

- generated test Maven validation passes
- target class line coverage improves

## Benchmark Status

| Status | Repo | Commit SHA | Maven command | Target Class | Before | After | Project Before | Project After | Repair Attempts | Generated Test Path | Artifact Path | Result |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| Completed | FasterXML/jackson-core | TBD | `mvn -q -DskipITs verify` | tools.jackson.core.io.DataOutputAsStream | 55.56% | 100.00% | 81.72% | 81.75% | 1 | `src/test/java/tools/jackson/core/unittest/io/DataOutputAsStreamGeneratedTest.java` | `.jtestgen/runs/<run-id>/` | Passed |
| Completed | Apache Commons CLI | `6f57cbe00e863a2754c4c7f0344640e27f39c494` | `mvn -q -DskipITs -Drat.skip=true verify` | org.apache.commons.cli.help.FilterHelpAppendable | 77.78% | 100.00% | 98.17% | 98.27% | 2 | `src/test/java/org/apache/commons/cli/help/FilterHelpAppendableGeneratedTest.java` | `.jtestgen/runs/20260527T001034037445Z-7b185d57/` | Passed |
| Planned | small Spring Boot service project | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Planned | Mockito-heavy service-layer project | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Planned | JTestGen demo legacy repo | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Planned | multi-module Maven project once supported | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

Example reports:

- [jackson-core report](examples/jackson-core-report.json)
- [commons-cli report](examples/commons-cli-report.json)

## Benchmark Template

| Field | Value |
| --- | --- |
| Repo | |
| Commit SHA | |
| Maven command | |
| Target class | |
| Baseline class coverage | |
| Final class coverage | |
| Baseline project coverage | |
| Final project coverage | |
| Repair attempts | |
| Generated test path | |
| Artifact path | |
| Notes | |

## Planned benchmark targets

- small Spring Boot service project
- Mockito-heavy service-layer project
- JTestGen demo legacy repo
- multi-module Maven project once supported
