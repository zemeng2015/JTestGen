# JTestGen

JTestGen is a coverage-guided AI system for generating Java unit tests. It combines JaCoCo coverage analysis, project-context retrieval, LLM-based test generation, Maven execution, repair-loop prompting, and run artifacts into one inspectable workflow.

The project is designed as an AI systems engineering demo: the model is only one component in a larger loop with evaluation, observability, deterministic fixtures, prompt versioning, and real Java repo validation.

## Highlights

- Coverage-guided target selection from JaCoCo XML.
- Prompt construction from target source, existing sample tests, project rules, and coverage data.
- Repair loop that feeds Maven failures back into the model.
- Run artifacts with prompt snapshots, Maven logs, generated revisions, and `report.json`.
- Prompt versioning for generation and repair prompts.
- Deterministic eval harness using a file-backed mock generator.
- Real demo on `FasterXML/jackson-core`: target class coverage improved from `55.56%` to `100.00%`.

## Project Guide

- [Architecture](docs/ARCHITECTURE.md)
- [Jackson-core demo](DEMO.md)
- [Example run report](docs/examples/jackson-core-report.json)

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

## What It Does

1. Runs baseline coverage with `mvn -q verify`.
2. Parses `target/site/jacoco/jacoco.xml`.
3. Selects the most uncovered suitable class, prioritizing classes with 0 covered lines while skipping interfaces, abstract classes, generated sources, inner classes, and other poor targets.
4. Finds the target source file under `src/main/java`.
5. Collects existing sample tests from `src/test/java`.
6. Loads project-specific generation rules from `--rules-file`, `TESTGEN_RULES.md`, `.testgen-rules.md`, or built-in defaults.
7. Builds a prompt with coverage data, source code, sample tests, and rules.
8. Writes one generated JUnit test under `src/test/java`.
9. Runs only the generated test with `mvn -q -Dtest=<GeneratedTestClass> test`.
10. If it fails, sends the generated test, source code, sample tests, rules, and Maven output back to the model for repair.
11. Repeats until the generated test passes or the repair limit is reached.
12. Runs final coverage with `mvn -q verify` and reports project and target-class coverage before/after.

## Assumptions

- The target project uses Maven.
- Maven is available on `PATH`.
- The target project has or can resolve test dependencies.
- Generated tests are JUnit 5 by default.
- JaCoCo report generation is available through the Maven JaCoCo plugin.

## Commands

Generate one coverage-guided test and run the repair loop:

```powershell
java-testgen run C:\path\to\java-project
```

For a demo, you can force a known class instead of using automatic lowest-coverage selection:

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

## Deterministic Eval

Run the local fixture eval without calling an LLM:

```powershell
python evals/run_eval.py --maven-command C:\tmp\apache-maven-3.9.11\bin\mvn.cmd
```

The eval uses a mock file-backed generator and reports compile success, repair attempts, target class, and coverage before/after.

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

## Notes

This tool writes generated tests into the target Java project. Use source control in the target project so you can review and keep only the useful tests.
