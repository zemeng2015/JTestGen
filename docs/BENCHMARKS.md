# Benchmarks

Benchmark results should demonstrate:

- real Java repositories
- reproducible Maven commands
- target class before/after coverage
- Maven pass/fail result
- repair attempts
- generated artifact path

## Benchmark Status

| Status | Repo | Commit SHA | Maven command | Target Class | Before | After | Project Before | Project After | Repair Attempts | Generated Test Path | Artifact Path | Result |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| Completed | FasterXML/jackson-core | TBD | `mvn -q -DskipITs verify` | tools.jackson.core.io.DataOutputAsStream | 55.56% | 100.00% | 81.72% | 81.75% | 1 | `src/test/java/tools/jackson/core/unittest/io/DataOutputAsStreamGeneratedTest.java` | `.jtestgen/runs/<run-id>/` | Passed |
| Planned | Apache Commons project | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Planned | small Spring Boot service project | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Planned | Mockito-heavy service-layer project | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Planned | multi-module Maven project once supported | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

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

- Apache Commons project
- small Spring Boot service project
- Mockito-heavy service-layer project
- multi-module Maven project once supported
