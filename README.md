# JTestGen

[![CI](https://github.com/zemeng2015/JTestGen/actions/workflows/ci.yml/badge.svg)](https://github.com/zemeng2015/JTestGen/actions/workflows/ci.yml)

AI Coverage Remediation Agent for Enterprise Java Teams

JTestGen helps Java teams systematically improve unit test coverage by combining JaCoCo-guided target selection, project-aware prompt construction, Maven-validated test generation, repair-loop prompting, and auditable run artifacts.

JTestGen is not a generic code completion tool. It is a workflow for turning Java coverage gaps into passing JUnit tests with measurable before/after coverage reports.

Copilot helps developers write tests faster.  
JTestGen helps teams remediate coverage gaps systematically.

## Why JTestGen?

- Coverage-guided: starts from JaCoCo coverage data, not random classes
- Maven-validated: generated tests must compile and pass
- Repair-loop enabled: failed tests are repaired using Maven output
- Auditable: stores prompts, Maven logs, generated revisions, and `report.json`
- Team-oriented: designed for repeatable coverage remediation workflows
- Local/BYOK friendly: supports OpenAI-compatible endpoints and can be adapted for private model endpoints

## Demo Result

| Repo | Target Class | Before | After | Maven Result |
| --- | --- | ---: | ---: | --- |
| FasterXML/jackson-core | `tools.jackson.core.io.DataOutputAsStream` | 55.56% | 100.00% | Passed |
| Apache Commons CLI | `org.apache.commons.cli.help.FilterHelpAppendable` | 77.78% | 100.00% | Passed |
| JTestGen demo legacy repo | `com.acme.billing.InvoiceCalculator` | 76.00% | 96.00% | Passed |
| Mockito-heavy service | `com.acme.orders.OrderFulfillmentService` | 61.90% | 100.00% | Passed |

See [DEMO.md](DEMO.md) for the full run details and artifacts.

## Try It / Request a Coverage Audit

Have a Java/Maven project with JaCoCo coverage gaps?

- Run JTestGen locally and review `.jtestgen/runs/<run-id>/report.json`
- Or open a [Coverage Audit Request issue](.github/ISSUE_TEMPLATE/coverage_audit_request.md)

## Project Guide

- [Architecture](docs/ARCHITECTURE.md)
- [Positioning](docs/POSITIONING.md)
- [Benchmarks](docs/BENCHMARKS.md)
- [Safety and limits](docs/SAFETY_AND_LIMITS.md)
- [Coverage audit offer](docs/COVERAGE_AUDIT_OFFER.md)
- [Enterprise roadmap](docs/ENTERPRISE_ROADMAP.md)
- [Example run report](docs/examples/jackson-core-report.json)

## 60-second mental model

JTestGen = JaCoCo target selection + project-aware prompt + Maven validation + repair loop + auditable artifacts.

## What JTestGen Does

1. Runs baseline `mvn verify`
2. Parses JaCoCo XML
3. Selects low-coverage target class
4. Builds project-aware prompt with source, sample tests, coverage data, and rules
5. Generates a JUnit test
6. Runs Maven test for the generated test
7. Repairs failures using Maven output
8. Runs final coverage
9. Writes `report.json` and run artifacts

## Quick Start

```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -e .

$env:OPENAI_API_KEY="..."
java-testgen run C:\path\to\java-project --target-coverage 0.80 --max-repairs 3
```

By default, the CLI calls `https://api.openai.com/v1/chat/completions` with `gpt-4o-mini`. You can override:

```powershell
$env:OPENAI_BASE_URL="https://your-compatible-endpoint/v1"
$env:OPENAI_MODEL="your-model"
```

## Sample Output

```text
Selected target: tools.jackson.core.io.DataOutputAsStream
Generated test passed
Class line coverage: 55.56% -> 100.00%
Project line coverage: 81.72% -> 81.75%
Artifacts written to: .jtestgen/runs/<run-id>/
```

## Commands

Generate one coverage-guided test and run the repair loop:

```powershell
java-testgen run C:\path\to\java-project
```

Force a known class instead of using automatic lowest-coverage selection:

```powershell
java-testgen run C:\path\to\java-project --target-class com.example.OrderService
```

Dry-run prompts without writing files or running Maven:

```powershell
java-testgen run C:\path\to\java-project --dry-run
```

Useful options:

```text
--class-glob        Glob under src/main/java, default **/*.java
--target-coverage  Minimum line coverage ratio, default 0.80
--max-repairs      Repair attempts for the generated test, default 3
--sample-tests      Existing test files to include as examples, default 3
--target-class      Optional fully qualified or simple class name for demo control
--rules-file        Optional file containing project-specific rules
--maven-command     Maven executable, for example mvn.cmd or C:\path\to\mvn.cmd
--verify-arg        Extra Maven argument for baseline/final verify, repeat as needed
--test-suffix      Generated test class suffix, default Test
--model            Override OPENAI_MODEL
```

## Run Artifacts

By default, every run writes an inspectable artifact bundle into the target Java project:

```text
.jtestgen/runs/<run-id>/
```

The bundle includes `report.json`, prompt snapshots, Maven logs, and generated test revisions. Use `--no-artifacts` to disable this.

See [docs/examples/jackson-core-report.json](docs/examples/jackson-core-report.json) for a real demo-shaped report.

## Safety Model

- Does not modify production source code
- Writes generated tests under `src/test/java`
- Stores all generated revisions
- Stores Maven logs and prompts for review
- Designed for human review before merge
- Does not claim semantic correctness beyond generated tests passing and coverage improvement

## Technical Assumptions

- The target project uses Maven.
- Maven is available on `PATH`, or provided with `--maven-command`.
- The target project has or can resolve test dependencies.
- Generated tests are JUnit 5 by default unless project rules or sample tests indicate otherwise.
- JaCoCo report generation is available through the Maven JaCoCo plugin.
- Project-specific generation rules can be loaded from `--rules-file`, `TESTGEN_RULES.md`, `.testgen-rules.md`, or built-in defaults.

## Supported Today

| Area | Status |
| --- | --- |
| Maven single-module projects | Supported |
| JaCoCo XML reports | Supported |
| JUnit-style test generation | Supported |
| OpenAI-compatible APIs | Supported |
| Maven repair loop | Supported |
| Run artifacts | Supported |
| Gradle projects | Not yet |
| Maven multi-module mapping | Not yet |
| Automatic build-file edits | Not yet |
| Patch-only PR mode | Planned |
| CI/GitHub Actions integration | Planned |

## Who This Is For

- Java teams with legacy Maven projects
- teams with JaCoCo coverage gates
- teams that need measurable coverage improvement
- consulting teams that need to deliver coverage improvements
- teams that want local/private endpoint AI workflows

## Not For

- replacing human review
- proving business correctness automatically
- generating arbitrary production code
- replacing full QA strategy
- projects without reproducible Maven test setup

## Deterministic Eval

Run the local fixture eval without calling an LLM:

```powershell
python evals/run_eval.py --maven-command C:\tmp\apache-maven-3.9.11\bin\mvn.cmd
```

The eval uses a mock file-backed generator and reports compile success, repair attempts, target class, and coverage before/after. It includes a direct-success case and a repair-needed case where the first generated test fails compilation and the repair response fixes it.

## Project Rules

You can add a rules file to the target Java repo:

```text
TESTGEN_RULES.md
```

Example:

```text
- Use AssertJ assertions.
- Do not use Mockito for value objects.
- Prefer @ExtendWith(MockitoExtension.class) for mocks.
- Keep tests package-private.
```

See [TESTGEN_RULES.example.md](TESTGEN_RULES.example.md) for a fuller example.

## Roadmap

Short-term:

- benchmark suite across 5+ Java projects
- batch mode for multiple target classes
- improved report summary
- GitHub Actions example workflow
- PR generation mode

Mid-term:

- Maven multi-module support
- Gradle support
- HTML dashboard
- team rules/profile support
- private endpoint deployment guide

Enterprise-oriented:

- Jenkins integration
- GitHub App / GitLab integration
- policy-based target selection
- coverage quality gates
- team audit logs
- private deployment package

## Call for Early Users

Looking for Java teams with low-coverage Maven projects. If you have a repo with JaCoCo coverage gaps, try JTestGen locally or open an issue for a free coverage audit.

## Notes

This tool writes generated tests into the target Java project. Use source control in the target project so you can review and keep only the useful tests.
