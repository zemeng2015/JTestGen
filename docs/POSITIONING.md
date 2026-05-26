# Positioning

## One-line positioning

JTestGen is an AI coverage remediation agent for enterprise Java teams.

## What it is

A workflow that converts JaCoCo coverage gaps into Maven-validated JUnit tests with repair loops and auditable artifacts.

## What it is not

- not a generic AI coding assistant
- not a replacement for Copilot/Cursor/Claude Code
- not a semantic correctness oracle
- not a full QA platform yet

## Why not just use Copilot?

A developer can use Copilot to write an individual test, but a team still needs:

- target selection from coverage data
- repeatable execution
- Maven validation
- repair loop
- before/after coverage reporting
- artifact tracking
- team rules
- CI integration
- human review workflow

JTestGen focuses on the workflow around coverage remediation: identify the coverage gap, build project-aware context, generate a test, validate it with Maven, repair failures, and preserve the evidence needed for review.

## Primary wedge

Coverage remediation for Java/Maven teams with JaCoCo coverage gaps.

## First customer profile

- 20-200 person Java software team
- Maven/Spring Boot legacy repo
- low test coverage
- coverage gate or quality KPI
- insufficient time to manually write tests
- needs measurable coverage improvement

## Commercial path

1. Open-source CLI
2. Free coverage audit
3. Paid coverage improvement PR package
4. CI integration
5. private/team/enterprise deployment
