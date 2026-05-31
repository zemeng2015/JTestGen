# MVP Scope

## MVP goal

Help one Java/Maven team turn selected JaCoCo coverage gaps into reviewable, Maven-passing JUnit test candidates with before/after coverage evidence.

## In scope

- Maven single-module projects
- JaCoCo XML coverage reports
- JUnit-style test generation
- OpenAI-compatible model endpoints
- project rules through `TESTGEN_RULES.md`
- source, related source, and sample test context
- Maven validation of generated tests
- repair loop using Maven output
- run artifacts with prompts, logs, generated revisions, `report.json`, and `summary.md`
- benchmark reports for credible examples
- manual service-assisted coverage audit
- patch output for generated tests
- processing multiple automatically selected targets in one run

## Out of scope for MVP

- Web UI
- SaaS accounts or hosted dashboard
- autonomous auto-merge
- semantic correctness guarantees
- automatic production source changes
- automatic dependency or `pom.xml` edits
- Gradle support
- full Maven multi-module support
- enterprise governance workflows
- GitHub App

## MVP workflow

1. User points JTestGen at a Maven project.
2. JTestGen runs baseline `mvn verify`.
3. JTestGen parses JaCoCo XML.
4. JTestGen selects or accepts a target class.
5. JTestGen builds prompt context from source, related sources, sample tests, coverage data, and rules.
6. JTestGen generates one test candidate.
7. JTestGen runs Maven for the generated test.
8. JTestGen repairs failures using Maven output.
9. JTestGen runs final coverage.
10. JTestGen writes artifacts and a before/after report.
11. JTestGen optionally writes a reviewable patch.
12. Human reviews the generated test before merge.

## MVP user promise

JTestGen will not promise that generated tests prove business correctness.

It will promise a narrower, useful outcome:

- identify coverage gaps
- generate reviewable test candidates
- validate them through Maven
- show measurable before/after coverage
- preserve artifacts for review

## First paid package

Coverage Improvement PR Package:

- target one Maven Java repository
- identify low-coverage candidates
- generate tests for 1-3 target classes
- run Maven validation and repair loop
- provide before/after coverage summary
- deliver as a patch or PR
- include run artifacts for review

Suggested first price: `$100-$300`.

## Acceptance criteria

A generated test candidate counts as successful only when:

- the target class coverage improves
- the generated test compiles
- the generated test passes Maven
- final `mvn verify` succeeds
- run artifacts are preserved
- a human can review the generated file

## What to build next

Priority order:

1. fifth benchmark: Spring Boot service demo
2. batch mode for multiple target classes
3. GitHub Actions example workflow
4. PR branch creation or GitHub CLI integration

Do not build Web UI until at least one real team has completed an audit or PR workflow.
