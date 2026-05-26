# Benchmarks

Benchmark results should demonstrate:

- real Java repositories
- reproducible Maven commands
- target class before/after coverage
- Maven pass/fail result
- repair attempts
- generated artifact path

| Repo | Target Class | Before | After | Project Before | Project After | Repair Attempts | Result |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| FasterXML/jackson-core | tools.jackson.core.io.DataOutputAsStream | 55.56% | 100.00% | 81.72% | 81.75% | 1 | Passed |

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

- FasterXML/jackson-core
- Apache Commons project
- small Spring Boot service project
- Mockito-heavy service-layer project
- multi-module Maven project once supported
